from django.urls import path
from .views import user_view,update_user_info,about_view,update_password,history_view


urlpatterns = [
    path("mine/",user_view,name="mine"),
    path("user/update/",update_user_info,name="update_user_info"),
    path("about/",about_view,name="about"),
    path("update_password/",update_password,name="update_password"),
    path("history/",history_view,name="history"),
]