from django.shortcuts import render
from login_app.models import User as user
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import os
from django.conf import settings
from datetime import datetime
from django.core.paginator import Paginator
from pay_app.models import Order as order
from django.db.models import Q
from datetime import timedelta

#获取当前月份
month = datetime.today().strftime("%m")

# Create your views here.
#处理用户页面的函数
@login_required
def user_view(request):
    #从user数据库中获取信息
    #获取名字
    username = user.objects.get(username=request.user).username
    #获取性别
    sex = user.objects.get(username=request.user).sex
    #获取介绍
    introduction = user.objects.get(username=request.user).introduction
    if sex == 'm':
        chenghu = '先生'
    else:
        chenghu = '女士'
    #获取头像
    avatar = user.objects.get(username=request.user).avatar
    #获取邮箱
    email = user.objects.get(username=request.user).email
    return render(request,'user.html',{'username':username,'sex':sex,'introduction':introduction,'chenghu':chenghu,'avatar':avatar,'email':email})

@csrf_exempt
@login_required
def update_user_info(request):
    if request.method == 'POST':
        try:
            current_user = user.objects.get(username=request.user)
            
            # 更新基本信息
            if 'username' in request.POST:
                current_user.username = request.POST['username']
            
            if 'sex' in request.POST:
                current_user.sex = request.POST['sex']
            
            if 'introduction' in request.POST:
                current_user.introduction = request.POST['introduction']
            
            # 处理头像上传
            if request.FILES.get('avatar'):
                current_user.avatar = request.FILES['avatar']
            
            current_user.save()
            
            return JsonResponse({
                'status': 'success',
                'message': '用户信息更新成功'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({
        'status': 'error',
        'message': '无效的请求方法'
    })




@login_required
def about_view(request):
    """
    关于页面视图，读取并显示 about.txt 文件内容
    """
    try:
        # 定义 about.txt 文件路径
        about_file_path = os.path.join(settings.BASE_DIR, 'static', 'about.txt')
        
        # 读取文件内容
        with open(about_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        return render(request, 'about.html', {'content': content})
    except FileNotFoundError:
        # 如果文件不存在，显示默认内容
        default_content = "医飞速达 v1.0.0\n智能医疗无人机配送系统\n\n关于我们：\n医飞速达致力于通过无人机技术改善医疗物资配送效率，为偏远地区和紧急医疗情况提供快速响应的配送服务。"
        return render(request, 'about.html', {'content': default_content})
    except Exception as e:
        # 处理其他异常
        error_content = f"读取关于文件时发生错误：{str(e)}"
        return render(request, 'about.html', {'content': error_content})


@login_required
def update_password(request):
    if request.method == 'POST':
        #获取用户密码
        try:
            old_password = user.objects.get(username=request.user).password
            if request.POST['old_password'] == old_password:
                user.objects.filter(username=request.user).update(password=request.POST['new_password'])
                return JsonResponse({
                    'status': 'success',
                    'message': '密码更新成功'
                })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
        

@login_required
def history_view(request):
    """统一的消费记录视图，通过查询参数获取页码"""
    
    # 从查询参数获取页码，默认为1
    page = request.GET.get('page', 1)
    
    # 获取筛选参数
    paymethod = request.GET.get('paymethod', '')
    time_range = request.GET.get('time_range', '')
    sort_by = request.GET.get('sort_by', '')
    
    # 从请求中获取用户名
    username = request.user.username
    order_buy = order.objects.filter(nickname=username)
    
    # 应用支付方式筛选
    if paymethod and paymethod != 'all_pay':
        order_buy = order_buy.filter(paymentMethod=paymethod)
    
    # 根据时间范围筛选
    if time_range and time_range != 'all':
        now = datetime.now()
        if time_range == 'month':
            order_buy = order_buy.filter(order_time__month=now.month, order_time__year=now.year)
        elif time_range == 'quarter':
            three_months_ago = now - timedelta(days=90)
            order_buy = order_buy.filter(order_time__gte=three_months_ago)
        elif time_range == 'year':
            one_year_ago = now - timedelta(days=365)
            order_buy = order_buy.filter(order_time__gte=one_year_ago)

    # 应用排序
    if sort_by:
        if sort_by == 'date-desc':
            order_buy = order_buy.order_by('-order_time')
        elif sort_by == 'date-asc':
            order_buy = order_buy.order_by('order_time')
        elif sort_by == 'price-desc':
            order_buy = order_buy.order_by('-order_time')  # 简化处理
        elif sort_by == 'price-asc':
            order_buy = order_buy.order_by('order_time')   # 简化处理
    else:
        order_buy = order_buy.order_by('-order_time')
    
    # 初始化分页器
    paginator = Paginator(order_buy, 5)
    history_data = paginator.get_page(page)  # 使用查询参数中的页码
    
    # 处理订单数据
    user_data = []
    total_cost = 0
    
    if history_data:
        for item in order_buy:
            if isinstance(item.items, list):
                price = 0
                name = ''
                for order_item in item.items:
                    price += order_item['price'] * order_item['quantity']
                    name += order_item['name'] + ','
                name = name.rstrip(',')
                
                user_data.append({
                    'name': name,
                    'notes': item.notes,
                    'price': round(price, 2),
                    'order_time': item.order_time,
                })
                total_cost += price

        total_cost = round(total_cost, 2)
        
        # 获取本月的消费
        now = datetime.now()
        this_month_orders = order_buy.filter(order_time__month=now.month, order_time__year=now.year)
        this_month_price = 0
        for order_item in this_month_orders:
            if isinstance(order_item.items, list):
                for item in order_item.items:
                    this_month_price += item.get('price', 0) * item.get('quantity', 0)
        
        # 获取购买次数统计
        buy_count = order_buy.count()
        this_month_buy_count = this_month_orders.count()
        
        # 获取最常使用的支付方式
        payment_methods = [item.paymentMethod for item in order_buy]
        if payment_methods:
            most_buy_pay = max(set(payment_methods), key=payment_methods.count)
        else:
            most_buy_pay = '暂无数据'
        
        # 应用排序到用户数据
        if sort_by:
            if sort_by == 'date-desc':
                user_data.sort(key=lambda x: x['order_time'], reverse=True)
            elif sort_by == 'date-asc':
                user_data.sort(key=lambda x: x['order_time'])
            elif sort_by == 'price-desc':
                user_data.sort(key=lambda x: x['price'], reverse=True)
            elif sort_by == 'price-asc':
                user_data.sort(key=lambda x: x['price'])
        
        # 只取当前页的数据
        start_index = (history_data.number - 1) * 5
        user_data = user_data[start_index:start_index + 5]
    
    # 渲染模板
    return render(request, 'history.html', {
        'history_data': user_data,
        'history_page': history_data,
        'total_price': total_cost,
        'this_month_price': this_month_price,
        'buy_count': buy_count,
        'this_month_buy_count': this_month_buy_count,
        'most_buy_kind': most_buy_pay,
        'paymethod_filter': paymethod,
        'time_range_filter': time_range,
        'sort_by_filter': sort_by,
    })