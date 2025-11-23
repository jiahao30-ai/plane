# actions.py
"""
动作空间定义模块
定义强化学习中可用的动作
"""

class ActionSpace:
    def __init__(self, hospitals_data):
        self.hospitals = hospitals_data
        self.num_hospitals = len(hospitals_data)
        self.action_descriptions = {}  #存储动作ID到描述的映射

        # 基本动作:选择每个医院
        for i,hospital in enumerate(hospitals_data):
            self.action_descriptions[i] = f"选择医院: {hospital.get('name', f'医院{i}')}"
        #特殊动作
        #当所有医院都没有足够库存时采取的动作
        self.action_descriptions[self.num_hospitals] = "等待补货"
        #当原定医院无法配送时采取的动作
        self.action_descriptions[self.num_hospitals + 1] = "重定向到替代方案"
        #当单个医院无法满足整个订单时采取的动作
        self.action_descriptions[self.num_hospitals + 2] = "拆分订单"
        self.action_size = self.num_hospitals + 3 #总动作数
    
    def get_action_description(self,action_id):
        """
        获取动作描述
        """
        return self.action_descriptions.get(action_id, f"未知动作: {action_id}")
    
    def execute_action(self, action_id, user_request, hospitals_data):
        """
        执行动作并提供选择理由

        Args:
            action_id: 动作ID
            user_request: 用户请求
            hospitals_data: 医院数据
        
        Returns:
            dict: 执行结果，包含动作信息和选择理由
        """
        if 0 <= action_id < self.num_hospitals:
            # 选择特定医院
            selected_hospital = hospitals_data[action_id]
            
            # 计算选择理由
            reasons = []
            
            # 距离因素
            distance = self._calculate_distance(
                user_request.get('latitude', 0),
                user_request.get('longitude', 0),
                selected_hospital.get('latitude', 0),
                selected_hospital.get('longitude', 0)
            )
            
            # 库存匹配度
            inventory_match = self._calculate_inventory_match(
                selected_hospital.get('inventory', {}),
                user_request.get('items', [])
            )
            
            # 构建选择理由
            if distance < 5:  # 5公里以内认为是近距离
                reasons.append("距离较近")
            elif distance < 15:  # 5-15公里认为是中等距离
                reasons.append("距离适中")
            else:
                reasons.append("距离较远但库存充足")
                
            if inventory_match >= 0.9:
                reasons.append("库存充足")
            elif inventory_match >= 0.5:
                reasons.append("库存部分满足需求")
            else:
                reasons.append("库存有限但为最优选择")
                
            return {
                'action': 'select_hospital',
                'hospital': selected_hospital,
                'hospital_id': selected_hospital.get('id'),
                'reasons': reasons,  # 添加选择理由
                'distance': distance,
                'inventory_match': inventory_match
            }
        elif action_id == self.num_hospitals:
            # 等待补货
            return {
                'action': 'wait_for_restock',
                'message': '等待医院补货',
                'reasons': ['所有医院库存不足，建议等待补货']
            }
        elif action_id == self.num_hospitals + 1:
            # 重定向到替代方案
            return {
                'action': 'redirect_alternative',
                'message': '重定向到替代配送方案',
                'reasons': ['无法找到合适的医院，需要重定向']
            }
        elif action_id == self.num_hospitals + 2:
            # 拆分订单
            return {
                'action': 'split_order',
                'message': '拆分订单到多个医院',
                'reasons': ['单个医院无法满足全部需求，需要拆分订单']
            }
        else:
            # 默认动作:选择第一个医院
            return {
                'action': 'select_hospital',
                'hospital': hospitals_data[0] if hospitals_data else None,
                'reasons': ['默认选择']
            }

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        计算两点间距离（使用Haversine公式）
        """
        from math import radians, sin, cos, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return 6371.0 * c

    def _calculate_inventory_match(self, hospital_inventory, order_items):
        """
        计算库存匹配度
        """
        if not order_items:
            return 1.0
            
        total_items = len(order_items)
        matched_items = 0
        
        for item in order_items:
            medicine_name = item.get('name', '')
            quantity_needed = item.get('quantity', 0)
            if medicine_name in hospital_inventory and hospital_inventory[medicine_name] >= quantity_needed:
                matched_items += 1
                
        return matched_items / total_items if total_items > 0 else 1.0
def create_action_space(hospitals_data):
    """Factory: create an ActionSpace for given hospitals data."""
    return ActionSpace(hospitals_data)

