from .views import chat_view,execute_image_text
from django.urls import path

urlpatterns = [
    path('chat/',chat_view,name='chat'),
    path('execute_image_text/',execute_image_text,name='execute_image_text'),
]