from django.urls import path
from .views import pay_view,submit_order,order_success,execute_success,cart_view,add_to_cart,update_cart_item,remove_from_cart,clear_cart,get_cart_info

urlpatterns = [
    path("pay_view/",pay_view,name="pay_view"),
    path("submit_order/",submit_order,name="submit_order"),
    path("order_success/",order_success,name="order_success"),
    path("execute_success/",execute_success,name="execute_success"),
    path("cart_view/", cart_view, name="cart_view"),
    path("add_to_cart/", add_to_cart, name="add_to_cart"),
    path("update_cart_item/", update_cart_item, name="update_cart_item"),
    path("remove_from_cart/", remove_from_cart, name="remove_from_cart"),
    path("clear_cart/", clear_cart, name="clear_cart"),
    path("cart_info/", get_cart_info, name="get_cart_info"),  # 添加新的URL
]