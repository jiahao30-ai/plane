from django.db import models
from shop_app.models import Medicine
# Create your models here.
class Hospital(models.Model):
    #节点名称
    name = models.CharField(max_length=50)
    #节点经度
    longitude = models.FloatField()
    #节点纬度
    latitude = models.FloatField()

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        verbose_name="配送站点"
        verbose_name_plural="配送站点"
        db_table = 'hospital'


#库存模型
class HospitalInventory(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ('hospital', 'medicine')
        verbose_name = "医院库存"
        verbose_name_plural = "医院库存"
        db_table = 'hospital_inventory'