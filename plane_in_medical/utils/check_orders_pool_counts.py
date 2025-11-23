import json
from collections import Counter
p = r"e:\PycharmProjects\plane_in_medical\plane_in_medical\data\data_pool_train.jsonl"
counter = Counter()
total = 0
with open(p,'r',encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        try:
            j=json.loads(line)
        except Exception:
            continue
        d=j.get('district') or j.get('区') or 'UNKNOWN'
        counter[d]+=1
        total+=1
print('total=', total)
for k,v in counter.most_common():
    print(k, v)
# print sample lines for non-未央区
print('\nSample non-未央区 entries:')
with open(p,'r',encoding='utf-8') as f:
    for line in f:
        j=json.loads(line)
        if j.get('district') and j.get('district') != '未央区':
            print(json.dumps(j, ensure_ascii=False))
            break
