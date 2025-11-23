import os
import re
import json
import glob
import random
from datetime import datetime, timedelta
from uuid import uuid4

"""
脚本功能介绍:
    从SQL模版中解析药品信息
    对已经有的订单进行增强(时间扰动,商品重采样,保证单订单商品总量上限并产生多个变体)
    并提供从SQL文件解析订单到JSONL的工具函数与命令行入口
"""
def parse_medicine_templates(sql_patterns):
    """
    从给定的SQL文件模式(excute*.sql)中提取药品id,name,price
    返回药品字典列表
    """
    meds = {}
    pattern = re.compile(r"UPDATE\s+medicine\s+SET\s+.*name='([^']+)'.*price=([0-9.]+).*WHERE\s+id=(\d+);", re.IGNORECASE)
    files = []
    for p in sql_patterns:
        files.extend(glob.glob(p))
    for f in sorted(set(files)):
        try:
            txt = open(f, 'r', encoding='utf-8').read()
        except Exception:
            continue
        for m in pattern.finditer(txt):
            name = m.group(1)
            price = float(m.group(2))
            mid = int(m.group(3))
            meds[mid] = {'id': mid, 'name': name, 'price': price}
    return list(meds.values())


def jitter_time(orig_time_str, max_days=30):
    '''
    对原始订单时间做随机扰动,增加时间多样性
    '''
    try:
        dt = datetime.strptime(orig_time_str, '%Y-%m-%d %H:%M:%S')
    except Exception:
        # if parsing fails, use now
        dt = datetime.now()
    delta_days = random.randint(-max_days, max_days)
    delta_hours = random.randint(-12, 12)
    delta_minutes = random.randint(-50, 50)
    ndt = dt + timedelta(days=delta_days, hours=delta_hours, minutes=delta_minutes)
    return ndt.strftime('%Y-%m-%d %H:%M:%S')


def normalize_items_total(items, max_total=5):
    """
    确保单个订单的所有商品数量之和不超过max_total,
    必要时减少某些商品数量或删除商品
    """
    items = [dict(i) for i in items]
    total = sum(int(i.get('quantity', 0)) for i in items)
    # if already within limit, return
    if total <= max_total:
        return items
    # reduce until fits
    tries = 0
    while total > max_total and tries < 1000:
        # try reduce quantity of an item that has qty>1
        idxs = [idx for idx, it in enumerate(items) if int(it.get('quantity', 0)) > 1]
        if idxs:
            idx = random.choice(idxs)
            items[idx]['quantity'] = int(items[idx]['quantity']) - 1
            if items[idx]['quantity'] <= 0:
                items.pop(idx)
        else:
            # remove a random item
            if not items:
                break
            items.pop(random.randrange(len(items)))
        total = sum(int(i.get('quantity', 0)) for i in items)
        tries += 1
    return items


def sample_items(med_templates, min_items=1, max_items=4, max_quantity=5, max_total_quantity=5):
    """
    从药品模版中随机抽取若干商品并分配数量，使得最终总量不超过max_total_quantity
    """
    if not med_templates:
        return []
    # attempt to sample a set of items and quantities that satisfy max_total_quantity
    attempts = 0
    while attempts < 50:
        k = random.randint(min_items, max_items)
        chosen = random.sample(med_templates, min(k, len(med_templates)))
        items = []
        total_q = 0
        for m in chosen:
            # choose qty but ensure we don't immediately exceed max_total
            remaining_slots = max_total_quantity - total_q
            if remaining_slots <= 0:
                break
            qty = random.randint(1, min(max_quantity, remaining_slots))
            items.append({'id': str(m['id']), 'name': m['name'], 'price': m['price'], 'quantity': qty})
            total_q += qty
        # normalize just in case
        items = normalize_items_total(items, max_total=max_total_quantity)
        if sum(int(i.get('quantity', 0)) for i in items) <= max_total_quantity and items:
            return items
        attempts += 1
    # fallback: choose single item with qty=min(max_total_quantity, max_quantity)
    m = random.choice(med_templates)
    return [{'id': str(m['id']), 'name': m['name'], 'price': m['price'], 'quantity': min(max_total_quantity, max_quantity)}]


def merge_items(existing, additions, max_total=5):
    """
    Merge two item lists by id. Quantities for same id are summed.
    Then normalize to ensure total quantity <= max_total.
    Returns a new list (does not mutate inputs).
    """
    if not existing:
        base = []
    else:
        base = [dict(i) for i in existing]
    add = [dict(i) for i in (additions or [])]
    idx = {str(i['id']): i for i in base}
    for a in add:
        aid = str(a.get('id'))
        try:
            aq = int(a.get('quantity', 0))
        except Exception:
            aq = 0
        if aid in idx:
            idx[aid]['quantity'] = int(idx[aid].get('quantity', 0)) + aq
        else:
            idx[aid] = {'id': aid, 'name': a.get('name'), 'price': a.get('price'), 'quantity': aq}
    merged = list(idx.values())
    merged = normalize_items_total(merged, max_total=max_total)
    return merged


def augment_orders(input_jsonl, excute_sql_patterns, out_jsonl, multiplier=5, max_days=30, max_total_quantity=5, seed=None, mode='replace', keep_coords=True):
    """
    对输入的订单JSONL生成多个变体并写入新的JSONL
    """
    if seed is not None:
        random.seed(seed)
    meds = parse_medicine_templates(excute_sql_patterns)
    os.makedirs(os.path.dirname(out_jsonl), exist_ok=True)
    total = 0
    with open(input_jsonl, 'r', encoding='utf-8') as fin, open(out_jsonl, 'w', encoding='utf-8') as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                order = json.loads(line)
            except Exception:
                continue
            # For each original order we will output 'multiplier' variants (including one canonical form)
            # Ensure that across these variants items total quantity <= max_total_quantity and that
            # the variants are not identical (since user coordinates are the same).
            variants = []
            # start with a normalized original: ensure its items also respect max_total_quantity
            orig = dict(order)
            # preserve original coordinates if present
            orig_lat = order.get('latitude')
            orig_lon = order.get('longitude')
            if isinstance(orig.get('items'), list):
                if mode == 'replace':
                    orig['items'] = normalize_items_total(orig['items'], max_total=max_total_quantity)
                else:
                    sampled = sample_items(meds, max_total_quantity=max_total_quantity)
                    orig['items'] = merge_items(orig.get('items', []), sampled, max_total=max_total_quantity)
            else:
                # if original items absent, sample one
                orig['items'] = sample_items(meds, max_total_quantity=max_total_quantity)
            # jitter original time too to add variety
            if 'order_time' in orig and orig['order_time']:
                orig['order_time'] = jitter_time(orig['order_time'], max_days=max_days)
            else:
                orig['order_time'] = jitter_time(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), max_days=max_days)
            variants.append(orig)
            # produce additional unique variants
            seen_signatures = set()
            def signature(itms):
                return tuple(sorted(((str(x.get('id')), int(x.get('quantity',0))) for x in itms)))

            seen_signatures.add(signature(orig['items']))
            attempts_per_variant = 50
            for i in range(multiplier - 1):
                success = False
                for attempt in range(attempts_per_variant):
                    ao = dict(order)
                    ao['order_id'] = f"{order.get('order_id','')}-aug{uuid4().hex[:6]}"
                    if 'order_time' in ao and ao['order_time']:
                        ao['order_time'] = jitter_time(ao['order_time'], max_days=max_days)
                    else:
                        ao['order_time'] = jitter_time(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), max_days=max_days)
                    # sample items respecting total quantity
                    sampled = sample_items(meds, max_total_quantity=max_total_quantity)
                    if mode == 'replace':
                        ao['items'] = sampled
                    else:
                        ao['items'] = merge_items(ao.get('items', []), sampled, max_total=max_total_quantity)
                    # ensure we do not change coordinates if requested
                    if keep_coords:
                        if orig_lat is not None:
                            ao['latitude'] = orig_lat
                        if orig_lon is not None:
                            ao['longitude'] = orig_lon
                    sig = signature(ao['items'])
                    if sig not in seen_signatures:
                        seen_signatures.add(sig)
                        # optional: status
                        ao['status'] = random.choice(['送货中', '已完成'])
                        variants.append(ao)
                        success = True
                        break
                if not success:
                    # as a fallback, slightly alter quantities of original to create variation
                    fallback = dict(orig)
                    # small deterministic tweak
                    if fallback['items']:
                        idx = random.randrange(len(fallback['items']))
                        fallback['items'][idx]['quantity'] = max(1, int(fallback['items'][idx]['quantity']) - 1)
                    fallback['order_id'] = f"{order.get('order_id','')}-aug{uuid4().hex[:6]}"
                    variants.append(fallback)

            # write out variants
            for v in variants:
                fout.write(json.dumps(v, ensure_ascii=False) + '\n')
                total += 1
    return total


def parse_order_sql_to_jsonl(sql_patterns, out_jsonl):
    """
    解析匹配模式的SQL文件中对order表的insert语句，把每个values元组转换为一行
    """
    files = []
    for p in sql_patterns:
        files.extend(glob.glob(p))
    files = sorted(set(files))
    os.makedirs(os.path.dirname(out_jsonl), exist_ok=True)
    total = 0
    with open(out_jsonl, 'w', encoding='utf-8') as fout:
        for f in files:
            try:
                txt = open(f, 'r', encoding='utf-8').read()
            except Exception:
                continue
            # find INSERT INTO `order` (col,...) VALUES ...; blocks
            for m in re.finditer(r"insert\s+into\s+`?order`?\s*\((?P<cols>[^)]+)\)\s*values\s*(?P<vals>.+?);",
                                 txt, flags=re.I | re.S):
                cols_raw = m.group('cols')
                vals_raw = m.group('vals').strip()
                cols = [c.strip().strip('`').strip() for c in cols_raw.split(',')]

                # split vals_raw into top-level tuple strings
                tuples = []
                cur = []
                depth = 0
                in_sq = False
                esc = False
                for ch in vals_raw:
                    cur.append(ch)
                    if ch == "'" and not esc:
                        in_sq = not in_sq
                    if ch == "\\" and not esc:
                        esc = True
                        continue
                    esc = False
                    if not in_sq:
                        if ch == '(':
                            depth += 1
                        elif ch == ')':
                            depth -= 1
                            if depth == 0:
                                # current tuple complete
                                t = ''.join(cur).strip()
                                tuples.append(t)
                                cur = []
                # if tuples still empty try simple split by '),('
                if not tuples and vals_raw:
                    # remove surrounding parentheses if present
                    vals = vals_raw
                    if vals.startswith('(') and vals.endswith(')'):
                        vals = vals[1:-1]
                    parts = re.split(r"\),\s*\(", vals, flags=re.S)
                    tuples = ['(' + p.strip() + ')' for p in parts if p.strip()]

                for tup in tuples:
                    # strip leading/trailing parentheses and possible trailing commas
                    t = tup.strip()
                    if t.startswith('(') and t.endswith(')'):
                        inner = t[1:-1]
                    else:
                        inner = t
                    # split fields by top-level commas (not inside quotes)
                    fields = []
                    curf = []
                    in_sq = False
                    esc = False
                    for ch in inner:
                        if ch == "'" and not esc:
                            in_sq = not in_sq
                        if ch == "\\" and not esc:
                            esc = True
                            curf.append(ch)
                            continue
                        if esc:
                            esc = False
                        if ch == ',' and not in_sq:
                            fields.append(''.join(curf).strip())
                            curf = []
                        else:
                            curf.append(ch)
                    if curf:
                        fields.append(''.join(curf).strip())

                    # map to cols
                    if len(fields) != len(cols):
                        # skip malformed
                        continue
                    obj = {}
                    for col, val in zip(cols, fields):
                        v = val
                        if v.upper() == 'NULL':
                            obj[col] = None
                            continue
                        v = v.strip()
                        # strip surrounding single quotes
                        if v.startswith("'") and v.endswith("'") and len(v) >= 2:
                            inner_val = v[1:-1]
                            # unescape single-quote represented by two single-quotes
                            inner_val = inner_val.replace("''", "'")
                            # try to detect json array (items)
                            if inner_val.startswith('[') and inner_val.endswith(']'):
                                try:
                                    obj[col] = json.loads(inner_val)
                                except Exception:
                                    obj[col] = inner_val
                            else:
                                obj[col] = inner_val
                        else:
                            # numeric?
                            try:
                                if '.' in v:
                                    obj[col] = float(v)
                                else:
                                    obj[col] = int(v)
                            except Exception:
                                obj[col] = v
                    fout.write(json.dumps(obj, ensure_ascii=False) + '\n')
                    total += 1
    return total


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Augment orders by varying order_time and items')
    parser.add_argument('--input', default=os.path.join(os.path.dirname(__file__), '..', 'data', 'orders_pool.jsonl'), help='Input JSONL of parsed orders')
    parser.add_argument('--excute', nargs='*', default=[os.path.join(os.path.dirname(__file__), '..', 'static', 'sql', 'excute*.sql')], help='excute SQL patterns')
    parser.add_argument('--out', default=os.path.join(os.path.dirname(__file__), '..', 'data', 'orders_augmented.jsonl'), help='Output augmented JSONL')
    parser.add_argument('--multiplier', type=int, default=5, help='How many variants per original (including original)')
    parser.add_argument('--mode', choices=['replace', 'add'], default='replace', help='How to handle items: replace original items or add sampled items')
    parser.add_argument('--keep-coords', action='store_true', help='Keep latitude/longitude exactly as original (do not modify)')
    parser.add_argument('--max-days', type=int, default=30, help='Max days to jitter order_time')
    parser.add_argument('--seed', type=int, help='Random seed')
    parser.add_argument('--parse-sql', action='store_true', help='Parse SQL order*.sql files into JSONL and exit')
    parser.add_argument('--sql-patterns', nargs='*', default=[os.path.join(os.path.dirname(__file__), '..', 'static', 'sql', 'order*.sql')], help='SQL file patterns to parse')
    parser.add_argument('--sql-out', default=os.path.join(os.path.dirname(__file__), '..', 'data', 'orders_from_sql.jsonl'), help='Output JSONL path for parsed SQL')
    args = parser.parse_args()

    inp = os.path.abspath(args.input)
    exc = args.excute
    outp = os.path.abspath(args.out)
    sql_patterns = args.sql_patterns
    sql_out = os.path.abspath(args.sql_out)
    if args.parse_sql:
        print(f'Parsing SQL patterns {sql_patterns} -> {sql_out}')
        cnt = parse_order_sql_to_jsonl(sql_patterns, sql_out)
        print(f'Parsed {cnt} rows to {sql_out}')
        raise SystemExit(0)
    print(f'Augmenting {inp} using {exc} -> {outp} (multiplier={args.multiplier}, mode={args.mode}, keep_coords={args.keep_coords})')
    n = augment_orders(inp, exc, outp, multiplier=args.multiplier, max_days=args.max_days, seed=args.seed, mode=args.mode, keep_coords=args.keep_coords)
    print(f'Wrote {n} orders to {outp}')
