from django.db import models
from time import time
class Order(models.Model):
    nickname = models.CharField(max_length=50,default="匿名用户")
    order_id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    province = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    #下单时间
    order_time = models.DateTimeField(default=time())
    #经纬度
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    district = models.CharField(max_length=50)
    notes = models.TextField(blank=True)
    paymentMethod = models.CharField(max_length=50)
    items = models.JSONField()
    #设置其默认值为送货中
    status = models.CharField(max_length=50, default="送货中")

    def __str__(self) -> str:
        return self.order_id
    
    class Meta:
        verbose_name = "订单"
        verbose_name_plural = "订单"
        db_table = "order"