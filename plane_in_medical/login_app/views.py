from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .models import User as user
from utils.captcha import generate_captcha
from django.http import HttpResponse
from io import BytesIO

# 判断登录函数
def login_view(request):
    # 如果是登录请求,即用户首次访问登录页面，则返回登录页面
    if request.method == 'GET':
        #如果初次访问登录页面,则不会显示error信息
        error_message = request.GET.get('error', '')
        return render(request, 'login.html', {'error_message': error_message})
    else :
        #判断验证码是否正确
        captcha = request.POST.get('captcha')
        if captcha.lower() != request.session.get('captcha_code').lower():
            return render(request, 'login.html', {'error_message': '验证码错误'})
        else :
            #post请求对输入的用户名和密码进行验证
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                #获取user中的属性is_superuser
                ks = user.is_superuser
                if ks == 1:
                    login(request, user)
                    #如果是超级用户则跳转到后台管理页面
                    return redirect('/admin/')
                else :
                    login(request, user)
                    return redirect('main')
            else :
                return render(request, 'login.html', {'error_message': '用户名或密码错误'})
#主页函数
#用户保护视图函数,确保只有经过身份验证的用户才能访问该视图
@login_required(login_url='/login/')
def main_view(request):
    return render(request, 'main.html')


#登出函数
def logout_view(request):
    #删除登录信息
    logout(request)
    return redirect('/login/')

#验证码函数
def captcha_view(request):
    image,code = generate_captcha()
    #保存验证码到session
    request.session['captcha_code'] = code
    #创建一个流文件
    stream = BytesIO()
    #将图片保存在流文件中
    image.save(stream,'png')
    #返回数据
    return HttpResponse(stream.getvalue())