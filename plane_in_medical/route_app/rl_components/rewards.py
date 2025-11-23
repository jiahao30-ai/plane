# rewards.py
"""
奖励函数定义模块
定义强化学习中奖励计算逻辑
"""
import math

class RewardFunction:
    def __init__(self):
        # ... (权重配置保持不变或根据新逻辑调整) ...
        self.weights = {
            # 选择医院时的即时奖励（基于库存匹配度和距离）
            'inventory_match': 50.0,      # 库存匹配度奖励系数 (降低)
            'distance_penalty': -1.0,     # 距离惩罚系数 (每 km) (降低)
            
            # 动作特定惩罚 (降低绝对值，使其影响更平滑)
            'wait_penalty': -50,          # 等待补货惩罚
            'split_order_penalty': -50,   # 拆单惩罚
            'redirect_penalty_base': -30, # 重定向基础惩罚
            'redirect_distance_penalty': -0.5, # 重定向额外距离惩罚 (每 km)

            # 配送效率奖励 (新增/调整)
            'time_efficiency': 0.5,       # 时间效率奖励系数 (每分钟节省)
            
            # 最终配送结果奖励 (降低绝对值，避免过度主导)
            'delivery_success_base': 200, # 成功配送基础奖励 (降低)
            'delivery_failure_penalty': -200, # 配送失败惩罚 (新增明确项)

            # 库存管理奖励 (新增，鼓励高效利用库存)
            'inventory_efficiency': 10.0, # 库存利用效率奖励 (每件满足的物品)
            'partial_fulfillment_bonus': 5.0, # 部分满足奖励系数
            
            # 用户体验相关 (可选，如果状态或结果中有相关信息)
            # 'user_satisfaction_bonus': 50, # 用户满意度奖励
        }
    
    def calculate_reward(self, action, state, next_state, execution_result):
        """
        计算奖励值
        Args:
            action: 执行的动作索引
            state: 执行前的状态向量
            next_state: 执行后的状态向量
            execution_result: 动作执行结果字典 (已增强)
        
        Returns:
            float: 奖励值
        """
        reward = 0.0

        # 1. 根据动作执行结果计算即时奖励 (可以利用新信息)
        # ... (select_hospital, wait_for_restock, split_order, redirect_alternative 的逻辑基本保持不变) ...
        # 但可以更精细地使用 execution_result 中的信息
        if execution_result.get('action') == 'select_hospital':
            # ... (原有逻辑) ...
            inventory_match = float(execution_result.get('hospital', {}).get('inventory_match', 0.0))
            distance_km = float(execution_result.get('hospital', {}).get('distance', 0.0))
            reward += self.weights['inventory_match'] * inventory_match
            reward += self.weights['distance_penalty'] * distance_km
            if inventory_match == 1.0:
                reward += 20.0 

        elif execution_result.get('action') == 'wait_for_restock':
            reward += self.weights['wait_penalty']
        
        elif execution_result.get('action') == 'split_order':
            reward += self.weights['split_order_penalty']
            # 可以根据拆单的复杂度（如分配的医院数）增加惩罚
            # assignments = execution_result.get('assignments', [])
            # reward += self.weights['split_order_penalty'] * len(assignments) * 0.1

        elif execution_result.get('action') == 'redirect_alternative':
             redirected_distance = float(execution_result.get('redirected_distance', 0.0))
             reward += self.weights['redirect_penalty_base']
             reward += self.weights['redirect_distance_penalty'] * redirected_distance
            
        # 2. 根据增强的配送结果计算最终奖励
        # 直接使用 execution_result 中的详细信息
        
        is_fully_satisfied = execution_result.get('is_fully_satisfied', False)
        # 简化失败判断：只要有未满足项且不是完全满足就是失败
        # 更精确的判断可能需要考虑 wait, redirect 失败等情况
        is_failure = execution_result.get('unfulfilled_items_count', 0) > 0 and not is_fully_satisfied 
        
        fulfilled_items = execution_result.get('fulfilled_items', 0)
        total_items = execution_result.get('total_items', 1) # 避免除以0
        travel_time = float(execution_result.get('estimated_travel_time', 0.0))

        # --- 应用最终奖励 ---
        if is_fully_satisfied:
            reward += self.weights['delivery_success_base']
            # 时间效率奖励：基准时间假设为 30 分钟，节省越多奖励越高
            time_saved = max(0.0, 30.0 - travel_time)
            reward += self.weights['time_efficiency'] * time_saved
            
        if is_failure: # 或者使用 unfulfilled_items_count > 0 作为条件
            reward += self.weights['delivery_failure_penalty']
            
        # 新增：库存效率奖励 (基于实际满足的物品数)
        reward += self.weights['inventory_efficiency'] * fulfilled_items
        
        # 新增：部分满足奖励 (鼓励满足尽可能多的物品，即使不完全)
        if not is_fully_satisfied and fulfilled_items > 0:
             partial_ratio = fulfilled_items / total_items
             reward += self.weights['partial_fulfillment_bonus'] * partial_ratio * 100 # 假设奖励与百分比相关

        return reward

# 单例实例
reward_function = RewardFunction()