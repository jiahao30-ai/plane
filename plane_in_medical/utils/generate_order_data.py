import re
import os
import json
import random
import glob
from datetime import datetime, timedelta
'''
脚本功能介绍:
    1. 解析SQL文件中的订单数据
    2. 将解析后的数据转换为json格式
    3. 可选择性地对订单时间进行随机扰动
    4. 将结果保存为JSONL文件(每行一个JSON对象)
'''

def _split_top_level_parentheses(s: str):
    """解析SQL语句中的VALUES部分,提取每个元组的内容"""
    tuples = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] == '(':
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                if s[j] == '(':
                    depth += 1
                elif s[j] == ')':
                    depth -= 1
                j += 1
            # s[i+1:j-1] is content inside parentheses
            tuples.append(s[i+1:j-1])
            i = j
        else:
            i += 1
    return tuples


def _parse_tuple_fields(tup: str):
    """把单个tuple字符串拆分成字段字符串列表"""
    fields = []
    i = 0
    n = len(tup)
    cur = []
    in_quote = False
    while i < n:
        ch = tup[i]
        if in_quote:
            if ch == "'":
                # handle doubled single-quote as escape
                if i + 1 < n and tup[i+1] == "'":
                    cur.append("'")
                    i += 2
                    continue
                else:
                    in_quote = False
                    i += 1
                    continue
            else:
                cur.append(ch)
                i += 1
                continue
        else:
            if ch == "'":
                in_quote = True
                i += 1
                continue
            if ch == ',':
                fields.append(''.join(cur).strip())
                cur = []
                i += 1
                continue
            else:
                cur.append(ch)
                i += 1
                continue
    # append last
    if cur:
        fields.append(''.join(cur).strip())
    # normalize SQL NULL -> None and remove surrounding whitespace
    norm = []
    for f in fields:
        if f.upper() == 'NULL':
            norm.append(None)
        else:
            norm.append(f)
    return norm


def _clean_sql_string(s: str):
    # 处理SQL字符串
    return s


def parse_order_sql(sql_path: str):
    #解析SQL文件
    #读取SQL文件
    text = open(sql_path, 'r', encoding='utf-8').read()
    #使用正则表达式匹配SQL语句
    m = re.search(r"insert into\s+`?order`?\s*\((.*?)\)\s*values\s*(.*);",
                  text, flags=re.IGNORECASE | re.S)
    if not m:
        raise RuntimeError('Could not find INSERT ... VALUES block for table `order`')
    #提取列名和值
    cols_str = m.group(1)
    vals_block = m.group(2)
    cols = [c.strip().strip('`') for c in cols_str.split(',')]
    #解析每个订单记录
    tuples = _split_top_level_parentheses(vals_block)
    orders = []
    #将数据转换为字典格式
    for tup in tuples:
        fields = _parse_tuple_fields(tup)
        if len(fields) != len(cols):
            # skip malformed
            continue
        rec = {}
        for k, v in zip(cols, fields):
            if v is None:
                rec[k] = None
                continue
            # if field was quoted, our parser already returned the inner content
            # decide conversion based on column name
            if k in ('latitude', 'longitude'):
                try:
                    rec[k] = float(v)
                except Exception:
                    rec[k] = None
            elif k == 'items':
                # items is a JSON string
                try:
                    rec[k] = json.loads(v)
                except Exception:
                    # attempt to fix single quotes
                    try:
                        rec[k] = json.loads(v.replace("'", '"'))
                    except Exception:
                        rec[k] = v
            else:
                rec[k] = v
        orders.append(rec)
    return orders


def jitter_order_time(ts_str: str, max_days: int = 30):
    #对原始的order_time字段进行随机扰动
    try:
        dt = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
    except Exception:
        # fallback: return original
        return ts_str
    #在原始时间基础上随机增减天数(+-30)
    delta_days = random.randint(-max_days, max_days)
    #随机增减小时数(+-12)
    delta_hours = random.randint(-12, 12)
    #随机增减分钟数(+-50)
    delta_minutes = random.randint(-50, 50)
    ndt = dt + timedelta(days=delta_days, hours=delta_hours, minutes=delta_minutes)
    return ndt.strftime('%Y-%m-%d %H:%M:%S')


def generate_from_sql(sql_path: str, out_path: str, jitter=True, max_days=15, limit=None):
    orders = parse_order_sql(sql_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as fout:
        count = 0
        for o in orders:
            if limit and count >= limit:
                break
            if 'order_time' in o and o['order_time'] and jitter:
                try:
                    o['order_time'] = jitter_order_time(o['order_time'], max_days=max_days)
                except Exception:
                    pass
            fout.write(json.dumps(o, ensure_ascii=False) + '\n')
            count += 1
    return count


def generate_from_sql_list(sql_paths, out_path: str, jitter=True, max_days=15, limit=None):
    """
    处理多个SQL文件的批量处理功能
    去重并验证文件存在性
    依次处理每个文件并合并输出
    """
    expanded = []
    for p in sql_paths:
        # expand glob patterns
        matched = glob.glob(p)
        if matched:
            expanded.extend(matched)
        elif os.path.isdir(p):
            # include all order*.sql in directory
            expanded.extend(sorted(glob.glob(os.path.join(p, 'order*.sql'))))
        else:
            expanded.append(p)

    # deduplicate while preserving order
    seen = set()
    files = []
    for p in expanded:
        ap = os.path.abspath(p)
        if ap not in seen and os.path.exists(ap):
            seen.add(ap)
            files.append(ap)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    total = 0
    with open(out_path, 'w', encoding='utf-8') as fout:
        for p in files:
            try:
                orders = parse_order_sql(p)
            except Exception as e:
                print(f'Warning: failed to parse {p}: {e}')
                continue
            for o in orders:
                if limit and total >= limit:
                    return total
                if 'order_time' in o and o['order_time'] and jitter:
                    try:
                        o['order_time'] = jitter_order_time(o['order_time'], max_days=max_days)
                    except Exception:
                        pass
                fout.write(json.dumps(o, ensure_ascii=False) + '\n')
                total += 1
    return total


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Parse static SQL order file and export JSONL orders pool')
    #指定单个SQL文件
    parser.add_argument('--sql', default=os.path.join(os.path.dirname(__file__), '..', 'static', 'sql', 'order.sql'), help='Path to SQL file')
    #指定多个SQL文件或通配符模式
    parser.add_argument('--sqls', nargs='*', help='Multiple SQL files or glob patterns to parse (overrides --sql)')
    #输出JSONL文件路径
    parser.add_argument('--out', default=os.path.join(os.path.dirname(__file__), '..', 'data', 'orders_pool.jsonl'), help='Output JSONL path')
    #禁用时间扰动功能
    parser.add_argument('--no-jitter', action='store_true', help='Disable jittering of order_time')
    #时间扰动的最大天数范围
    parser.add_argument('--max-days', type=int, default=15, help='Max days for jitter')
    #限制导出的订单数量
    parser.add_argument('--limit', type=int, help='Limit number of orders exported')
    args = parser.parse_args()

    out_path = os.path.abspath(args.out)
    if args.sqls:
        # expand relative paths
        sql_inputs = [os.path.abspath(s) for s in args.sqls]
        print(f'Parsing multiple SQL files {sql_inputs} -> {out_path}')
        n = generate_from_sql_list(sql_inputs, out_path, jitter=not args.no_jitter, max_days=args.max_days, limit=args.limit)
    else:
        sql_path = os.path.abspath(args.sql)
        print(f'Parsing {sql_path} -> {out_path}')
        n = generate_from_sql(sql_path, out_path, jitter=not args.no_jitter, max_days=args.max_days, limit=args.limit)
    print(f'Wrote {n} orders to {out_path}')
