from django.urls import path
from .views import order_execute,delete_order,delete_all_orders

urlpatterns = [
    path("order_execute/",order_execute,name="order_execute"),
    path("delete_order/<str:order_id>",delete_order,name="delete_order"),
    path("delete_all_orders/",delete_all_orders,name="delete_all_orders"),
]