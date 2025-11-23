import requests
import json
from typing import Tuple, Optional
import math
class XiAnGeocoder:
    def __init__(self, api_key: str = None):
        """
        初始化西安地理编码器
        
        Args:
            api_key: 百度地图API密钥，如果未提供则使用默认密钥
        """
        # 默认使用的百度地图API密钥
        self.api_key = "api_key"
        self.base_url = "路径"
        
    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        获取西安市内地点的精确经纬度
        
        Args:
            address: 地点地址（例如：西安交通大学、大雁塔等）
            
        Returns:
            Tuple[float, float]: (经度, 纬度) 或 None（如果未找到）
        """

            
        # 构建请求参数
        params = {
            'address': address,
            'city': '西安市',
            'output': 'json',
            'ak': self.api_key
        }
        
        try:
            # 发送请求到百度地图API
            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status()
            
            # 解析响应
            data = response.json()
            
            # 检查状态码
            if data.get('status') == 0:
                result = data.get('result')
                if result:
                    location = result.get('location')
                    if location:
                        longitude = location.get('lng')
                        latitude = location.get('lat')
                        # 验证坐标是否在西安市范围内
                        if self._is_in_xian(longitude, latitude):
                            return (longitude, latitude)
                        else:
                            print(f"地址 '{address}' 的坐标不在西安市范围内")
                            return None
            else:
                print(f"地理编码失败，状态码: {data.get('status')}")
                return None
                
        except requests.RequestException as e:
            print(f"请求错误: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
        except Exception as e:
            print(f"未知错误: {e}")
            return None
    
    def _is_in_xian(self, longitude: float, latitude: float) -> bool:
        """
        检查坐标是否在西安市范围内
        
        Args:
            longitude: 经度
            latitude: 纬度
            
        Returns:
            bool: 如果在西安市范围内返回True，否则返回False
        """
        # 西安市大致的经纬度范围
        # 经度范围: 108.45 - 109.50
        # 纬度范围: 33.75 - 34.80
        return (108.45 <= longitude <= 109.50 and 
                33.75 <= latitude <= 34.80)
    def _get_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两个经纬度坐标之间的距离（使用Haversine公式）
        
        Args:
            lat1: 第一个点的纬度
            lon1: 第一个点的经度
            lat2: 第二个点的纬度
            lon2: 第二个点的经度
            
        Returns:
            float: 两点之间的距离（单位：公里）
        """
        # 地球半径（公里）
        R = 6371.0
        
        # 将角度转换为弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 计算差值
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine公式
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # 计算距离
        distance = R * c
        return distance
    def test_distance_calculation(self):
        """
        测试距离计算功能
        """
        # 测试用例：西安交通大学第一附属医院到西安庆华医院
        xjtu_lat, xjtu_lon = 34.219570, 108.936741  # 西安交通大学第一附属医院
        qh_lat, qh_lon = 34.315833, 109.069722      # 西安庆华医院
        
        distance = self._get_distance(xjtu_lat, xjtu_lon, qh_lat, qh_lon)
        print(f"西安交通大学第一附属医院到西安庆华医院的距离: {distance:.2f} 公里")
        
        # 测试用例：西安交通大学第一附属医院到西安高新医院
        xg_lat, xg_lon = 34.216667, 108.866667      # 西安高新医院
        distance2 = self._get_distance(xjtu_lat, xjtu_lon, xg_lat, xg_lon)
        print(f"西安交通大学第一附属医院到西安高新医院的距离: {distance2:.2f} 公里")
    

# 测试代码
if __name__ == "__main__":
    # 示例使用
    geocoder = XiAnGeocoder()
    
    # 测试单个地址
    test_addresses = [
        "西安市阎良区郑家湾路8号",
    ]
    
    for addr in test_addresses:
        coords = geocoder.get_coordinates(addr)
        if coords:
            print(f"{addr}: 经度={coords[0]:.6f}, 纬度={coords[1]:.6f}")
        else:
            print(f"{addr}: 未找到坐标")
