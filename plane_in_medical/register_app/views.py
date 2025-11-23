from django.shortcuts import render,redirect
from login_app.models import User
#注册用户
def register_view(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    elif request.method == 'POST':
        # 处理注册逻辑
        username = request.POST.get('username')
        password = request.POST.get('password')
        #上传头像
        avatar = request.FILES.get('avatar')
        sex = request.POST.get('sex') or 'm'
        email = request.POST.get('email')
        index = True
        #对输入的字段进行判断
        if len(username) < 1 or len(username) > 5:
            index = False
            return render(request, 'register.html', {'error_message': '用户名长度不符合要求,必须在1到5个字符之间'})
        if len(password) < 6 or len(password) > 16:
            index = False
            return render(request, 'register.html', {'error_message': '密码长度不符合要求,必须在6到16个字符之间'})
        if not email:
            index = False
            return render(request, 'register.html', {'error_message': '邮箱不能为空'})
        #将用户信息加载到数据库中
        if index:
            try:
                user = User.objects.create_user(username=username,password=password,sex=sex,email=email,avatar=avatar)
                return redirect('login')
            except Exception as e:
                return render(request, 'register.html', {'error_message': '用户名已存在'})