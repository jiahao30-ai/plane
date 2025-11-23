from .views import paginator_view,medicine_view,comment_view,post_comment,delete_comment
from django.urls import path

urlpatterns = [
    path('medicine/', medicine_view),
    path('medicine/<int:page_num>/', paginator_view),
    path('medicine/<int:id>/inscription/',comment_view),
    path('medicine/<int:id>/comment/',post_comment,name='post_comment'),
    path('medicine/<int:id>/delete/',delete_comment,name='delete_comment'),
]