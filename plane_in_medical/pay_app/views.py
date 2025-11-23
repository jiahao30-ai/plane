from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from shop_app.models import Medicine as medicine
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
import uuid
import time
from .models import Order
from utils.shopping_cart import ShoppingCartService

from utils.get_position import XiAnGeocoder
@login_required
def submit_order(request):
    if request.method == 'POST':
        try:
            #获取订单数据
            order_data = json.loads(request.POST.get('order_data', '{}'))
            #获取当前登录用户的用户名
            nickname = request.user.username
            print(nickname)
            order_id = str(int(time.time())) + str(uuid.uuid4().hex)[:6]
            
            # 确保时间字段是正确的字符串格式或者使用 datetime 对象
            from datetime import datetime
            current_time = datetime.now()
            # 构建完整地址
            full_address = f"{order_data['province']}{order_data['city']}{order_data['district']}{order_data['address']}"
            #根据full_address获取经纬度
            geocoder = XiAnGeocoder()
            latitude, longitude = geocoder.get_coordinates(full_address)
            #经纬度分别保留6位小数
            latitude = round(latitude, 6)
            longitude = round(longitude, 6)
            #创建订单
            order = Order.objects.create(
                order_id=order_id, 
                name=order_data['name'], 
                phone=order_data['phone'],
                address=order_data['address'], 
                city=order_data['city'],
                district=order_data['district'], 
                longitude=latitude,
                latitude=longitude,
                province=order_data['province'],
                notes=order_data['notes'], 
                paymentMethod=order_data['paymentMethod'],
                items=order_data['items'],
                nickname=nickname,
                order_time=current_time  
            )
            return JsonResponse({'status': 'success', 'order_id': order.order_id})
        except Exception as e:
            print("错误信息：", str(e))
            import traceback
            traceback.print_exc()  # 打印完整的错误堆栈信息
            return JsonResponse({'status': 'error', 'message': '提交失败'})

@login_required
#/order_success/?order_id=
def order_success(request):
    order_id = request.GET.get('order_id', '')
    return render(request, 'order_success.html', {'order_id': order_id})

@login_required
def execute_success(request):
    if request.method == 'POST':
        try:
            # 获取订单ID
            data = json.loads(request.body.decode('utf-8'))
            order_id = data.get('order_id', '')
            print("订单ID:", order_id)
            order = Order.objects.get(order_id=order_id)
            if order:
                #修改status为已完成
                order.status = '已完成'
                order.save()
                return JsonResponse({'status': 'ok'})
        except Order.DoesNotExist:
            #订单不存在,返回错误信息
            return JsonResponse({'status': '订单没有找到'})
        except Exception as e:
            #其他错误,返回错误信息
            print("错误信息：", str(e))
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

#=======================================================================================
@login_required
def cart_view(request):
    """显示购物车页面"""
    #创建购物车服务实例
    cart_service = ShoppingCartService(request.user.id)
    #获取购物车商品
    cart_items = cart_service.get_cart_items()
    
    # 为每个商品计算总价
    for item in cart_items:
        # 确保商品包含必需的字段
        if 'price' in item and 'quantity' in item:
            item['total_price'] = item['price'] * item['quantity']
        else:
            # 如果缺少必要字段，设置默认值
            item['total_price'] = 0.0
            if 'price' not in item:
                item['price'] = 0.0
            if 'quantity' not in item:
                item['quantity'] = 1
    #计算购物车总价
    total_price = sum(item['total_price'] for item in cart_items)

    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})

@require_POST
@login_required
def add_to_cart(request):
    """添加商品到购物车"""
    try:
        data = json.loads(request.body)
        medicine_id = data.get('medicine_id')
        quantity = data.get('quantity')
        #创建购物车服务实例
        print("用户ID:", request.user.id)
        cart_service = ShoppingCartService(request.user.id)
        #添加商品到购物车
        if cart_service.add_item(medicine_id, quantity):
            return JsonResponse({
                'status': 'success',
                'message': '商品已经添加到购物车',
                'item_count': cart_service.get_item_count()
            })
        else :
            return JsonResponse({
                'status': 'error',
                'message': '添加商品失败'
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@require_POST
@login_required
def update_cart_item(request):
    """更新购物车商品数量"""
    try:
        data = json.loads(request.body)
        medicine_id = data.get('medicine_id')
        quantity = data.get('quantity')
        #创建购物车服务实例
        cart_service = ShoppingCartService(request.user.id)
        # 更新商品数量
        if cart_service.update_quantity(medicine_id, quantity):
            return JsonResponse({
                'status': 'success',
                'message': '购物车已更新',
                'total_price': cart_service.get_total_price(),
                'item_count': cart_service.get_item_count()
            })
        else :
            return JsonResponse({
                'status': 'error',
                'message': '更新失败'
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@require_POST
@login_required
def remove_from_cart(request):
    """
    从购物车移除商品
    """
    try:
        data = json.loads(request.body)
        medicine_id = data.get('medicine_id')

        # 创建购物车服务实例
        cart_service = ShoppingCartService(request.user.id)

        #移除商品
        if cart_service.remove_item(medicine_id):
            return JsonResponse({
                'status': 'success',
                'message': '商品已移除',
                'total_price': cart_service.get_total_price(),
                'item_count': cart_service.get_item_count()
            })
        else :
            return JsonResponse({
                'status': 'error',
                'message': '移除失败'
            }
            )
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def clear_cart(request):
    """
    清空购物车
    """
    try:
        #创建购物车服务实例
        cart_service = ShoppingCartService(request.user.id)
        #清空购物车
        cart_service.clear_cart()

        return JsonResponse({
            'status': 'success',
            'message': '购物车已清空'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def get_cart_info(request):
    """
    获取购物车信息（商品数量等）
    """
    try:
        # 创建购物车服务实例
        cart_service = ShoppingCartService(request.user.id)
        # 获取购物车商品数量
        item_count = cart_service.get_item_count()
        
        return JsonResponse({
            'status': 'success',
            'item_count': item_count
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def pay_view(request):
    """结算页面"""
    # 检查是否是POST请求（来自购物车页面）
    if request.method == 'POST':
        # 获取商品的id
        # 使用getlist获取数据
        medicine_ids = request.POST.getlist('medicine_ids[]')
        car = []
        for id in medicine_ids:
            # 获取药品名字
            name = medicine.objects.get(id=id).name
            # 获取介绍
            introduction = medicine.objects.get(id=id).introduction
            # 获取价格
            price = medicine.objects.get(id=id).price
            # 获取图片
            image = medicine.objects.get(id=id).image
            car.append({'name': name, 'introduction': introduction, 'price': price, 'image': image})
        return render(request, 'pay.html', {'medicine_ids': car})
    
    # GET请求，从购物车获取商品
    # 创建购物车服务实例
    cart_service = ShoppingCartService(request.user.id)
    # 获取购物车商品
    cart_items = cart_service.get_cart_items()
    # 如果购物车为空,重定向到购物车页面
    if not cart_items:
        return redirect('cart_view')
    
    return render(request, 'pay.html', {'medicine_ids': cart_items})