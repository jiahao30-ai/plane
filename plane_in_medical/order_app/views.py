from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from pay_app.models import Order
from route_app.models import Hospital
from django.http import JsonResponse
import json
from utils.get_position import XiAnGeocoder
'''
订单信息:
订单id:order_id,
收货人:name,
区域:province+city+district,
详细地址:address,
备注:notes,
配送物资:items['name']
配送物资数量:items['quantity']
价格:items['price']*items['quantity']
配送状态:status
'''

@login_required
def order_execute(request):
    #获取当前用户的所有订单并返回json格式数据
    nickname = request.user.username
    orders = Order.objects.filter(nickname=nickname)
    orders_data = []
    # 判断请求是否为Ajax请求，如果是则返回JSON数据
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        for order in orders:
            #计算总价格和商品总数
            total_amount = 0
            total_items = 0
            #处理订单项
            items_details = []
            if isinstance(order.items,list):
                for item in order.items:
                    quantity = item.get('quantity', 0)
                    price = item.get('price', 0)
                    total_amount += quantity * price
                    total_items += quantity
                    items_details.append({
                        'name': item.get('name', ''),
                        'quantity': quantity,
                        'price': price,
                    })
            
            orders_data.append({
                'id': order.order_id,
                'customer_name': order.name,
                'full_address': f"{order.province} {order.city} {order.district} {order.address}",
                'notes': order.notes,
                'amount': total_amount,
                'item_count': total_items,
                'items': items_details,
                'status': order.status,
            })
        return JsonResponse({'orders': orders_data},safe=False)
    return render(request, 'order_execute.html')


# 删除订单
@login_required
def delete_order(request, order_id):  # order_id 现在是字符串类型
    if request.method == 'POST':
        try:
            # 使用 order_id 字段查找订单（假设 Order 模型使用 order_id 作为主键字段）
            order = Order.objects.get(order_id=order_id)  # 修改为 order_id 字段
            order.delete()
            return JsonResponse({'status': 'success'})
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': '订单不存在'}, status=404)
        except Exception as e:
            print("错误信息：", str(e))
            return JsonResponse({'status': 'error', 'message': '服务器内部错误'}, status=500)
#删除当前用户中的全部订单
@login_required
def delete_all_orders(request):
    if request.method == 'POST':
        try:
            #nickname就是用户名
            nickname  = request.user.username
            orders = Order.objects.filter(nickname=nickname)
            orders.delete()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

