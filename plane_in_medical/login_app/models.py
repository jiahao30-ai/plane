from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
# Create your models here.
class User(AbstractUser):
    # 用户名
    username = models.CharField(_('用户名'), max_length=150, unique=True)
    # 密码
    password = models.CharField(_('密码'), max_length=128)
    # 性别
    sex = models.CharField(_('性别'), max_length=1, choices=[('m', '男'), ('f', '女')], default='m')
    # 个性签名
    introduction = models.TextField(verbose_name='个性签名')
    #上传头像
    avatar = models.ImageField(upload_to='avatar/', verbose_name='头像')
    # 邮箱
    email = models.EmailField(unique=True, verbose_name='邮箱')


    def __str__(self):
        return self.username
    
    class Meta:
        #数据库中的表名
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name  
 

