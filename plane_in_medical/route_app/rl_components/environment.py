# environment.py
"""
强化学习环境定义
模拟无人机配送环境
"""
import numpy as np
from .states import state_space
from .actions import create_action_space
from .rewards import reward_function
import copy  # 引入 copy 模块


class DroneDeliveryEnvironment:
    def __init__(self, hospitals_data):
        # 保存原始医院数据的深拷贝作为模板，用于每次 reset 时创建独立副本
        self._hospitals_data_template = copy.deepcopy(hospitals_data)
        # self.hospitals_data 将在 reset 中被初始化为模板的副本
        self.hospitals_data = None
        self.state = None
        self.action_space = create_action_space(self._hospitals_data_template) # 使用模板创建 action_space
        self.state_space = state_space
        self._user_request = None
        self._order_medicines = None

    def reset(self, user_request, order_medicines):
        """
        重置环境
        """
        self._user_request = user_request
        self._order_medicines = order_medicines
        # 每次 reset 时，都从模板创建一个新的医院数据副本，确保库存独立
        self.hospitals_data = copy.deepcopy(self._hospitals_data_template)
        # 重新创建 action_space，因为它依赖于 hospitals_data (虽然当前实现可能不需要，但更安全)
        # self.action_space = create_action_space(self.hospitals_data) 
        self.state = self.state_space.build_state_vector(
            user_request, self.hospitals_data, order_medicines
        )
        return self.state
    def step(self, action):
        """
        执行动作并返回结果
        """
        # 1. 调用 action_space 执行动作 (不修改 self.hospitals_data)
        execution_result = self.action_space.execute_action(
            action, self._user_request or {}, self.hospitals_data # 传入副本
        )

        # 2. 计算订单总物品数 (通用信息)
        total_order_items = sum(int(it.get('quantity', 1)) for it in self._order_medicines or [])
        execution_result['total_items'] = total_order_items

        # 3. 根据动作类型，补充详细信息并可能修改 self.hospitals_data 副本
        # --- 库存更新逻辑 (修改部分) ---
        if execution_result.get('action') == 'select_hospital' and execution_result.get('hospital'):
            hosp = execution_result['hospital']
            # ... (计算距离 distance_km 和库存匹配 inventory_match 的代码保持不变) ...
            # 计算距离
            try:
                from math import radians, sin, cos, asin, sqrt
                lon1 = float(self._user_request.get('longitude', 0.0) or 0.0)
                lat1 = float(self._user_request.get('latitude', 0.0) or 0.0)
                lon2 = float(hosp.get('longitude', 0.0) or 0.0)
                lat2 = float(hosp.get('latitude', 0.0) or 0.0)
                lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                c = 2 * asin(sqrt(a))
                distance_km = 6371.0 * c
            except Exception:
                distance_km = 0.0

            # 计算库存匹配度
            inv = hosp.get('inventory', {}) or {}
            ordered = self._order_medicines or []
            match_count = 0
            total = 0
            for it in ordered:
                total += 1
                key = it.get('name') or str(it.get('id'))
                need = int(it.get('quantity', 1))
                have = int(inv.get(key, 0))
                if have >= need:
                    match_count += 1
            inventory_match = (match_count / total) if total > 0 else 0

            # 将计算结果附加到 hospital 对象（这是副本中的对象）
            hosp['distance'] = distance_km
            hosp['inventory_match'] = inventory_match

            # determine if hospital can fully fulfill the order
            fully_sufficient = inventory_match == 1.0
            execution_result['sufficient_inventory'] = fully_sufficient

            # --- 增强 execution_result 信息 ---
            execution_result['estimated_travel_time'] = distance_km # 简化估算
            execution_result['hospital_id'] = hosp.get('id')
            execution_result['distance_km'] = distance_km # 显式添加距离

            # 如果能够完全满足，则从该医院库存中扣除所需数量（持久化到 self.hospitals_data 副本）
            if fully_sufficient:
                # ... (查找并修改副本中医院库存的代码保持不变，但稍作调整以获取 target_hosp_obj) ...
                 # find the hospital object inside self.hospitals_data (副本) that matches hosp by id or coordinates
                hid = hosp.get('id')
                target_hosp_obj = None
                for hobj in self.hospitals_data:
                    if hid is not None and hobj.get('id') == hid:
                        target_hosp_obj = hobj
                        break
                if target_hosp_obj is None:
                    # fallback: try to match by coordinates
                    for hobj in self.hospitals_data:
                        if float(hobj.get('latitude', 0) or 0) == float(hosp.get('latitude', 0) or 0) and \
                           float(hobj.get('longitude', 0) or 0) == float(hosp.get('longitude', 0) or 0):
                            target_hosp_obj = hobj
                            break

                if target_hosp_obj is not None:
                    # 直接修改 self.hospitals_data 副本中的库存
                    inv_to_modify = target_hosp_obj.get('inventory', {})
                    for it in self._order_medicines or []:
                        key = it.get('name') or str(it.get('id'))
                        need = int(it.get('quantity', 1))
                        prev = int(inv_to_modify.get(key, 0))
                        inv_to_modify[key] = max(0, prev - need)
                    # 更新副本中的库存字典
                    target_hosp_obj['inventory'] = inv_to_modify
                    execution_result['decremented'] = True
                    
                    # --- 增强 execution_result 信息 (完全满足情况) ---
                    execution_result['fulfilled_items'] = total_order_items
                    execution_result['unfulfilled_items_count'] = 0
                    execution_result['is_fully_satisfied'] = True
                    execution_result['travel_minutes'] = distance_km
                else:
                    execution_result['decremented'] = False
                    # 如果找不到医院对象，可能需要特殊处理或标记错误
                    # 这里简单处理，认为未满足
                    execution_result['fulfilled_items'] = 0
                    execution_result['unfulfilled_items_count'] = total_order_items
                    execution_result['is_fully_satisfied'] = False
                    execution_result['travel_minutes'] = distance_km # 即使失败也可能飞行
            else:
                # 库存不满足
                execution_result['decremented'] = False
                # --- 增强 execution_result 信息 (部分满足或不满足情况) ---
                # 估算满足的物品数 (基于 inventory_match)
                execution_result['fulfilled_items'] = int(total_order_items * inventory_match)
                execution_result['unfulfilled_items_count'] = total_order_items - execution_result['fulfilled_items']
                execution_result['is_fully_satisfied'] = False
                execution_result['travel_minutes'] = distance_km # 即使不满足也可能飞行

        elif execution_result.get('action') == 'wait_for_restock':
            # ... (模拟补货并修改 self.hospitals_data 副本的代码保持不变) ...
            # 简单模拟：对所有医院中缺少的物品补货少量 (修改副本)
            for hobj in self.hospitals_data: # 修改副本
                inv = hobj.get('inventory', {}) or {}
                for it in self._order_medicines or []:
                    key = it.get('name') or str(it.get('id'))
                    if int(inv.get(key, 0)) < int(it.get('quantity', 1)):
                        inv[key] = int(inv.get(key, 0)) + 5  # 补货5件
                hobj['inventory'] = inv # 更新副本
            
            execution_result['restocked'] = True
            
            # --- 增强 execution_result 信息 ---
            execution_result['estimated_travel_time'] = 0.0
            execution_result['hospital_id'] = None
            execution_result['travel_minutes'] = 0
            # wait 动作本身不直接满足物品，所以 fulfilled_items 通常为 0
            execution_result['fulfilled_items'] = 0
            execution_result['unfulfilled_items_count'] = total_order_items # 暂时未满足
            execution_result['is_fully_satisfied'] = False

        elif execution_result.get('action') == 'redirect_alternative':
            # ... (查找替代医院并修改 self.hospitals_data 副本库存的代码保持不变，但稍作调整) ...
             # 找到最近且库存足够的医院并执行派单 (修改副本库存)
            user_lon = float(self._user_request.get('longitude', 0.0) or 0.0)
            user_lat = float(self._user_request.get('latitude', 0.0) or 0.0)
            best = None
            best_dist = None
            for idx, hobj in enumerate(self.hospitals_data): # 使用副本
                # compute distance
                try:
                    from math import radians, sin, cos, asin, sqrt
                    lon2 = float(hobj.get('longitude', 0.0) or 0.0)
                    lat2 = float(hobj.get('latitude', 0.0) or 0.0)
                    lon1, lat1, lon2r, lat2r = map(radians, [user_lon, user_lat, lon2, lat2])
                    dlon = lon2r - lon1
                    dlat = lat2r - lat1
                    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2r) * sin(dlon / 2) ** 2
                    c = 2 * asin(sqrt(a))
                    dist = 6371.0 * c
                except Exception:
                    dist = 1e9

                # check sufficiency (使用副本库存)
                inv = hobj.get('inventory', {}) or {}
                ok = True
                for it in self._order_medicines or []:
                    key = it.get('name') or str(it.get('id'))
                    need = int(it.get('quantity', 1))
                    if int(inv.get(key, 0)) < need:
                        ok = False
                        break
                if ok and (best is None or dist < best_dist):
                    best = hobj
                    best_dist = dist
                    
            if best is not None:
                # perform decrement on best (修改副本库存)
                for it in self._order_medicines or []:
                    key = it.get('name') or str(it.get('id'))
                    need = int(it.get('quantity', 1))
                    prev = int(best.get('inventory', {}).get(key, 0))
                    best.setdefault('inventory', {})[key] = max(0, prev - need) # 修改副本
                
                execution_result['redirected_to'] = best.get('id')
                execution_result['redirected_distance'] = best_dist
                execution_result['hospital_id'] = best.get('id')
                
                # --- 增强 execution_result 信息 (重定向成功) ---
                execution_result['estimated_travel_time'] = best_dist
                execution_result['fulfilled_items'] = total_order_items # 重定向成功意味着完全满足
                execution_result['unfulfilled_items_count'] = 0
                execution_result['is_fully_satisfied'] = True
                execution_result['travel_minutes'] = best_dist
            else:
                execution_result['redirected_to'] = None
                execution_result['hospital_id'] = None
                
                # --- 增强 execution_result 信息 (重定向失败) ---
                execution_result['estimated_travel_time'] = 0.0
                execution_result['fulfilled_items'] = 0
                execution_result['unfulfilled_items_count'] = total_order_items
                execution_result['is_fully_satisfied'] = False
                execution_result['travel_minutes'] = 0

        elif execution_result.get('action') == 'split_order':
            # ... (拆单并修改 self.hospitals_data 副本库存的代码保持不变，但稍作调整) ...
            # 分配订单到多家医院：对每个物品按医院顺序尝试扣减 (修改副本库存)
            assignments = []
            for it in self._order_medicines or []:
                need = int(it.get('quantity', 1))
                key = it.get('name') or str(it.get('id'))
                remaining = need
                # try to fulfill from hospitals in order (使用副本)
                for hobj in self.hospitals_data:
                    if remaining <= 0:
                        break
                    have = int(hobj.get('inventory', {}).get(key, 0))
                    if have <= 0:
                        continue
                    take = min(have, remaining)
                    # 修改副本库存
                    hobj.setdefault('inventory', {})[key] = have - take
                    assignments.append({'hospital_id': hobj.get('id'), 'item': key, 'qty': take})
                    remaining -= take
                # record if fully assigned
                if remaining > 0:
                    execution_result.setdefault('unfulfilled_items', []).append({'item': key, 'remaining': remaining})
            execution_result['assignments'] = assignments
            
            # --- 增强 execution_result 信息 (拆单) ---
            execution_result['hospital_id'] = None
            execution_result['travel_minutes'] = 0 # 拆单旅行时间复杂，暂时设为0或累加
            execution_result['estimated_travel_time'] = 0.0 # 拆单旅行时间复杂，暂时设为0或累加
            # 计算满足的物品数
            fulfilled_count = sum(a.get('qty', 0) for a in assignments)
            execution_result['fulfilled_items'] = fulfilled_count
            execution_result['unfulfilled_items_count'] = total_order_items - fulfilled_count
            # 如果没有未满足项，则认为是成功的
            execution_result['is_fully_satisfied'] = (execution_result['unfulfilled_items_count'] == 0)

        # --- 库存更新逻辑结束 ---

        # 4. 计算下一个状态
        next_state = self.state_space.build_state_vector(
            self._user_request, self.hospitals_data, self._order_medicines
        )
        
        # 5. 计算奖励 (奖励函数现在可以使用增强后的 execution_result)
        reward = reward_function.calculate_reward(
            action, self.state, next_state, execution_result
        )
        
        # 6. 检查是否完成 (单步决策问题)
        done = True
        
        # 7. 更新状态
        self.state = next_state

        # 8. 返回结果 (包含增强的 execution_result)
        return next_state, reward, done, execution_result

    def render(self):
        """
        渲染环境状态(可选)
        """
        pass

# 环境工厂函数 (保持不变)
def create_environment(hospitals_data):
    return DroneDeliveryEnvironment(hospitals_data)
