from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import re
# Create your models here.
#创建药品表单

class Medicine(models.Model):
    #药品分类
    kind = models.CharField(max_length=20)
    #药品名称
    name = models.CharField(max_length=20)
    #药品图片
    image = models.ImageField(upload_to='medicine_images/')
    #药品简介
    introduction = models.TextField()
    #药品价格
    price = models.FloatField()

    def __str__(self):
        return self.name
    
    @property
    def full_image_url(self):
        """
        返回完整的图片URL，如果是云存储URL则直接返回，否则返回本地URL
        """
        if self.image:
            image_path = str(self.image)
            # 检查是否是完整的HTTP/HTTPS URL
            if re.match(r'^https?://', image_path):
                return image_path
            else:
                # 如果是本地路径，返回完整的本地URL
                return self.image.url
        return ''
    
    class Meta:
        db_table = 'medicine'
        verbose_name = '药品'
        verbose_name_plural = verbose_name

#创造评论药品的表单
class Comment(models.Model):
    #评论人姓名,与user表关联
    name = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    #评论内容
    content = models.TextField()
    #评论药品的id,与meidicine表关联
    medicine_id = models.ForeignKey(Medicine,on_delete=models.CASCADE,null=True)


    class Meta:
        db_table = 'comment'
        verbose_name = '评论'
        verbose_name_plural = verbose_name