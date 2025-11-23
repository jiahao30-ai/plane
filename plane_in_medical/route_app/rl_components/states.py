"""
状态空间定义模块
定义强化学习中使用的状态表示
"""

import math


class StateSpace:
    def __init__(self):
        # 增加状态向量维度以容纳更多信息
        # 原有 2 (用户位置) + 5*4 (5个医院*4特征) = 22
        # 新增 2 (订单信息) + 5*2 (5个医院新增特征) + 2 (全局信息) = 14
        # 总计 22 + 14 = 36
        self.state_dimensions = 36  

    def build_state_vector(self, user_request, hospital_data, order_medicines):
        """
        构建状态向量

        参数:
            user_request: 用户请求信息
            hospital_data: 所有医院数据
            order_medicines: 订单中的药品信息
        
        返回:
            list:状态向量
        """
        features = []
        
        # 1. 用户位置特征(2维)
        features.extend([
            float(user_request.get('latitude', 0)),
            float(user_request.get('longitude', 0))
        ])

        # 2. 订单信息特征(2维)
        total_order_quantity = sum(int(item.get('quantity', 0)) for item in order_medicines)
        order_item_types = len(order_medicines)
        features.extend([total_order_quantity, order_item_types])

        # 3. 医院特征(前5个最相关的医院,每个医院6个特征)
        sorted_hospitals = self._sort_hospitals_by_relevance(
            user_request, hospital_data, order_medicines
        )[:5]
        
        top_hospital_distances = [] # 用于计算全局信息
        
        for hospital in sorted_hospitals:
            hospital_features = self._extract_hospital_features(
                hospital, order_medicines, user_request
            )
            # 新增特征：医院总库存量、与订单匹配的药品总库存量
            hospital_inventory = hospital.get('inventory', {})
            total_inventory = sum(hospital_inventory.values())
            matching_inventory = sum(
                hospital_inventory.get(item.get('name'), 0) * int(item.get('quantity', 0))
                for item in order_medicines
            )
            hospital_features.extend([total_inventory, matching_inventory])
            
            features.extend(hospital_features)
            top_hospital_distances.append(hospital_features[3]) # 索引3是距离
            
        # 填充未达到5个医院的情况
        while len(features) < 2 + 2 + 5 * 6: # 用户位置(2) + 订单信息(2) + 5医院*(纬度,经度,匹配度,距离,总库存,匹配库存)
            features.extend([0, 0, 0, 0, 0, 0]) # 用0填充医院特征

        # 4. 全局信息特征(2维)
        # 最近医院的距离、库存最充足的医院的匹配库存量
        min_distance = min(top_hospital_distances) if top_hospital_distances else 0
        max_matching_inventory = max(
            (f for i, f in enumerate(features[6:]) if i % 6 == 5), default=0
        ) # 从医院特征中提取匹配库存量(索引5)
        features.extend([min_distance, max_matching_inventory])

        # 5. 填充或截取到固定长度
        while len(features) < self.state_dimensions:
            features.append(0)
        
        return features[:self.state_dimensions]
    
    def _sort_hospitals_by_relevance(self, user_request, hospital_data, order_medicines):
        """
        根据相关性排序医院
        """
        def relevance_score(hospital):
            # 距离分数(越近越高分)
            distance = self._calculate_distance(
                user_request.get('latitude', 0),
                user_request.get('longitude', 0),
                hospital.get('latitude', 0),
                hospital.get('longitude', 0)
            )
            distance_score = 1000 / (1 + distance)

            # 库存匹配分数
            inventory_score = self._calculate_inventory_match_score(
                hospital.get('inventory', {}), order_medicines)
            
            return inventory_score * 100 + distance_score
        
        return sorted(hospital_data, key=relevance_score, reverse=True)
    
    def _extract_hospital_features(self, hospital, order_medicines, user_request):
        """
        提取单个医院的特征
        [纬度, 经度, 库存匹配分数, 距离]
        """
        return [
            float(hospital.get('latitude', 0)),
            float(hospital.get('longitude', 0)),
            self._calculate_inventory_match_score(
                hospital.get('inventory', {}), order_medicines
            ),
            self._calculate_distance(
                float(user_request.get('latitude', 0)),
                float(user_request.get('longitude', 0)),
                float(hospital.get('latitude', 0)),
                float(hospital.get('longitude', 0))
            )
        ]
    
    def _calculate_inventory_match_score(self, hospital_inventory, order_medicines):
        """
        计算库存匹配分数
        """
        if not order_medicines:
            return 0
        match_count = 0
        total_required = 0
        for medicine in order_medicines:
            required_qty = int(medicine.get('quantity', 0))
            available_qty = int(hospital_inventory.get(medicine.get('name', ''), 0))

            if available_qty >= required_qty:
                match_count += 1
            total_required += 1
        return match_count / max(total_required, 1) if total_required > 0 else 0
    
    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """
        距离计算
        """
        try:
            lon1, lat1, lon2, lat2 = map(math.radians, [lng1, lat1, lng2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.asin(math.sqrt(a))
            return 6371.0 * c
        except Exception:
            return 0.0
    
# 单例实例
state_space = StateSpace()