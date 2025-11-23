from .views import get_route,check_order
from django.urls import path

urlpatterns = [
    
    path('route/', get_route,name='route'),
    path('check_order/', check_order,name='check_order'),
]