#引入path
from django.urls import path
from .views import login_view,main_view,captcha_view,logout_view

urlpatterns = [
    path('login/',login_view,name='login'),
    path('main/',main_view,name='main'),
    path('captcha/',captcha_view,name='captcha'),
    path('logout/',logout_view,name='logout'),
]