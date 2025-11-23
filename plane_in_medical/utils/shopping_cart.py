# utils/shopping_cart.py
import redis
import json
from django.conf import settings
from shop_app.models import Medicine

class ShoppingCartService:
    def __init__(self, user_id):
        self.user_id = user_id
        self.redis_client = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.cart_key = f"cart:{user_id}"
    
    def add_item(self, medicine_id, quantity):
        """添加商品到购物车"""
        try:
            # 获取商品信息
            medicine = Medicine.objects.get(id=medicine_id)
            medicine_data = {
                'id': medicine.id,
                'name': medicine.name,
                'price': float(medicine.price),
                'introduction': medicine.introduction,
                'image': medicine.full_image_url if hasattr(medicine, 'full_image_url') else str(medicine.image.url) if medicine.image else '',
                'quantity': int(quantity)  # 确保quantity字段存在
            }
            
            # 检查商品是否已在购物车中
            existing_item = self.redis_client.hget(self.cart_key, medicine_id)
            if existing_item:
                # 如果已存在，更新数量
                item_data = json.loads(existing_item)
                item_data['quantity'] = int(item_data.get('quantity', 0)) + int(quantity)
                medicine_data = item_data
            
            # 保存到Redis
            self.redis_client.hset(self.cart_key, medicine_id, json.dumps(medicine_data))
            return True
        except Medicine.DoesNotExist:
            return False
        except Exception as e:
            print(f"添加商品到购物车失败: {e}")
            return False
    
    def remove_item(self, medicine_id):
        """从购物车移除商品"""
        return self.redis_client.hdel(self.cart_key, medicine_id)
    
    def update_quantity(self, medicine_id, quantity):
        """更新商品数量"""
        if quantity <= 0:
            return self.remove_item(medicine_id)
        
        item = self.redis_client.hget(self.cart_key, medicine_id)
        if item:
            item_data = json.loads(item)
            item_data['quantity'] = int(quantity)
            self.redis_client.hset(self.cart_key, medicine_id, json.dumps(item_data))
            return True
        return False
    
    def get_cart_items(self):
        """获取购物车所有商品"""
        items = self.redis_client.hgetall(self.cart_key)
        cart_items = []
        for item_json in items.values():
            try:
                item_data = json.loads(item_json)
                # 确保quantity字段存在
                if 'quantity' not in item_data:
                    item_data['quantity'] = 1
                if 'price' not in item_data:
                    item_data['price'] = 0.0
                cart_items.append(item_data)
            except json.JSONDecodeError:
                continue
        return cart_items
    
    def get_item_count(self):
        """获取购物车商品总数"""
        return self.redis_client.hlen(self.cart_key)
    
    def get_total_price(self):
        """计算购物车总价"""
        items = self.get_cart_items()
        total = 0
        for item in items:
            total += item.get('price', 0.0) * item.get('quantity', 1)
        return total
    
    def clear_cart(self):
        """清空购物车"""
        return self.redis_client.delete(self.cart_key)
    
    def exists(self, medicine_id):
        """检查商品是否在购物车中"""
        return self.redis_client.hexists(self.cart_key, medicine_id)