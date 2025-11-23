from django.contrib import admin

# Register your models here.
#注册用户模型

from .models import User

admin.site.register(User)

