from django.shortcuts import render
from shop_app.models import Medicine as medicine
from django.contrib.auth.decorators import login_required
# Create your views here.
@login_required
def search_view(request):
    #从medicine中获取要搜索的数据
    medicine_list = medicine.objects.all()
    #从前端拿到搜索的数据内容
    keyword = request.GET.get('q')
    if keyword:
        medicine_list = medicine_list.filter(name__contains=keyword)
        #直接传递模型实例而不是values
        medicine_data = medicine_list
    else :
        medicine_data = []
    return render(request, 'search.html',{'medicine_data':medicine_data})