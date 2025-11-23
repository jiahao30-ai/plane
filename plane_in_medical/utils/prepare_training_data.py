from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import math
import random
import numpy as np
import datetime


"""
为强化学习模型准备训练，验证和测试数据
从订单数据:data_pool_train.jsonl和医院数据hospitals.json出发,
经过一系列处理,最终生成适合强化学习智能体使用的特征数据和辅助信息
"""

def haversine(lon1, lat1, lon2, lat2):
    """
    使用Haversine公式计算两个经纬度坐标之间的球面距离(公里)
    """
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return 6371.0 * c


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """
    逐行读取.jsonl文件,每行一个JSON对象
    并将所有成功解析的对象存入列表返回
    """
    data = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except Exception:
                continue
    return data


def load_hospitals(path: Path) -> List[Dict[str, Any]]:
    """
    读取包含医院数据的JSON文件,返回解析后的Python列表
    """
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def extract_time_features(ts_str: str) -> Tuple[int, int, int]:
    """
    时间提取,从订单的时间戳中提取三个特征
        Hour: 小时(0-23)
        weekday: 星期几(0=周一,6=周日)
        is_weekend: 是否是周末(1=是,0=否)
    """
    try:
        dt = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
    except Exception:
        try:
            dt = datetime.datetime.fromisoformat(ts_str)
        except Exception:
            # fallback: now
            dt = datetime.datetime.utcnow()
    hour = dt.hour
    weekday = dt.weekday()
    is_weekend = 1 if weekday >= 5 else 0
    return hour, weekday, is_weekend


def build_item_vocab(orders: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    遍历所有订单中的药品,构建一个唯一的商品名称/ID到整数索引的映射字典
    优先使用商品的name,如果没有则使用id,索引从1开始
    """
    items = set()
    for o in orders:
        for it in o.get('items', []):
            # prefer item name if present, else id
            key = it.get('name') or str(it.get('id'))
            items.add(key)
    item2idx = {it: idx + 1 for idx, it in enumerate(sorted(items))}  # reserve 0 for padding
    return item2idx


def encode_items(order_items: List[Dict[str, Any]], item2idx: Dict[str, int], max_len: int) -> Tuple[List[int], List[float]]:
    """
    将一个订单中的商品列表转换为两个固定长度的列表
        idxs: 商品对应的索引列表
        qtys: 对应商品的数量列表
    """
    idxs = []
    qtys = []
    for it in order_items:
        key = it.get('name') or str(it.get('id'))
        idx = item2idx.get(key)
        if idx is None:
            continue
        idxs.append(idx)
        qtys.append(float(it.get('quantity', 1)))
    if len(idxs) >= max_len:
        return idxs[:max_len], qtys[:max_len]
    else:
        pad = [0] * (max_len - len(idxs))
        padf = [0.0] * (max_len - len(qtys))
        return idxs + pad, qtys + padf






    