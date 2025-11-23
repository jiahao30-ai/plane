"""
URL configuration for plane_in_medical project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path,include
from login_app.urls import urlpatterns as login_urlpatterns
from register_app.urls import urlpatterns as register_urlpatterns
from route_app.urls import urlpatterns as route_urlpatterns
from communicate_app.urls import urlpatterns as communicate_urlpatterns
from shop_app.urls import urlpatterns as shop_urlpatterns
from order_app.urls import urlpatterns as order_urlpatterns
from user_app.urls import urlpatterns as user_urlpatterns
from pay_app.urls import urlpatterns as pay_urlpatterns
from search_app.urls import urlpatterns as search_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(login_urlpatterns)),
    path("", include(register_urlpatterns)),
    path("", include(route_urlpatterns)),
    path("", include(communicate_urlpatterns)),
    path("", include(shop_urlpatterns)),
    path("", include(order_urlpatterns)),
    path("", include(user_urlpatterns)),
    path("", include(pay_urlpatterns)),
    path("", include(search_urlpatterns)),
    path("set_language/", set_language, name="set_language"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

