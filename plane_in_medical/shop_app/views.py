

from django.shortcuts import render
from .models import Medicine
from django.core.paginator import Paginator
from .models import Comment as comment
from login_app.models import User as user
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_page

@login_required
@cache_page(60 * 15)  # 缓存15分钟
def medicine_view(request):
    #获取筛选参数
    kind = request.GET.get('kind', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort_by', 'default')
    
    #获得第一页的数据
    medicine_list = Medicine.objects.all()
    
    # 应用筛选条件
    if kind:
        medicine_list = medicine_list.filter(kind=kind)
    if min_price:
        medicine_list = medicine_list.filter(price__gte=min_price)
    if max_price:
        medicine_list = medicine_list.filter(price__lte=max_price)
    
    # 应用排序
    if sort_by == 'price-asc':
        medicine_list = medicine_list.order_by('price')
    elif sort_by == 'price-desc':
        medicine_list = medicine_list.order_by('-price')
    elif sort_by == 'name-asc':
        medicine_list = medicine_list.order_by('name')
    elif sort_by == 'name-desc':
        medicine_list = medicine_list.order_by('-name')
    else:
        medicine_list = medicine_list.order_by('id')
    
    #初始化分页器
    paginator = Paginator(medicine_list, 8)
    medicine_data = paginator.get_page(1)
    
    #传递筛选参数到模版
    context = {
        'medicine_data': medicine_data,
        'kind_filter': kind,
        'min_price_filter': min_price,
        'max_price_filter': max_price,
        'sort_by_filter': sort_by
    }
    return render(request,'medicine.html',context)

@login_required
@cache_page(60 * 15)  # 缓存15分钟
#实现分页效果
def paginator_view(request, page_num):
    #获取筛选参数
    kind = request.GET.get('kind', '')
    min_price = request.GET.get('min_price','')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort_by', 'default')
    
    #获取medicine表中的所有数据
    medicine_list = Medicine.objects.all()
    
    #应用筛选条件
    if kind:
        medicine_list = medicine_list.filter(kind=kind)
    if min_price:
        medicine_list = medicine_list.filter(price__gte=min_price)
    if max_price:
        medicine_list = medicine_list.filter(price__lte=max_price)
    
    #应用排序
    if sort_by == 'price-asc':
        medicine_list = medicine_list.order_by('price')
    elif sort_by == 'price-desc':
        medicine_list = medicine_list.order_by('-price')
    elif sort_by == 'name-asc':
        medicine_list = medicine_list.order_by('name')
    elif sort_by == 'name-desc':
        medicine_list = medicine_list.order_by('-name')
    else :
        medicine_list = medicine_list.order_by('id')

    #初始化分页器
    paginator = Paginator(medicine_list, 8)
    #获取指定页码的数据
    medicine_data = paginator.get_page(page_num)
    
    # 传递筛选参数给模版
    context = {
        'medicine_data': medicine_data,
        'kind_filter': kind,
        'min_price_filter': min_price,
        'max_price_filter': max_price,
        'sort_by_filter': sort_by,
    }
    #返回数据
    return render(request,'medicine.html',context)

@login_required
#获取药品对应的详细介绍
def comment_view(request,id):
    #获取类型
    kind = Medicine.objects.get(id=id).kind
    #根据获取id 获取名字
    medicine_name = Medicine.objects.get(id=id)
    #获取图片
    image = Medicine.objects.get(id=id).image
    #获取介绍
    introduction = Medicine.objects.get(id=id).introduction
    #根据id从comment表中获取数据
    #获取评论内容
    commentxs = comment.objects.filter(medicine_id=id).select_related('name')  # 全部评论
    context = {
        'kind'          : kind,
        'medicine_name' : medicine_name,
        'image'         : image,
        'introduction'  : introduction,
        'commentxs'     : commentxs,      # ← 关键：名字跟模板一致
    }
    return render(request, 'comment.html', {'medicine': medicine_name, 'context': context})

@login_required
@require_POST
def post_comment(request, id):
    medicine = Medicine.objects.get(pk=id)
    print(medicine)
    text = request.POST.get('text', '').strip()
    print(text)
    if not text:
        return JsonResponse({'ok': False, 'msg': '内容不能为空'})
    # 创建评论
    c = comment.objects.create(
        medicine_id=medicine,
        name_id=request.user.id,          # 当前登录用户
        content=text
    )
    # 把这条评论的 HTML 片段返回，方便前端直接插入
    html = f'''
    <div class="comment">
        <img class="avatar" src="{c.name.avatar.url}" alt="">
        <div class="info">
            <div class="username">{c.name.username}</div>
            <div class="content">{c.content}</div>
        </div>
    </div>
    '''
    return JsonResponse({'ok': True, 'html': html})

#删除自己发的评论操作
@login_required
@require_http_methods(["DELETE"])   # 允许 DELETE
def delete_comment(request, id):
    c = get_object_or_404(comment, pk=id)   # 这条评论
    if c.name_id != request.user.id:        # 只能删自己的
        return JsonResponse({'ok': False, 'msg': '无权删除'}, status=403)

    c.delete()
    return JsonResponse({'ok': True})