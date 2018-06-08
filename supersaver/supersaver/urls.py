"""supersaver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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


from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path

from product import views as product_views

web_1_0_urlpatterns = [
    url(r'^offers/$', product_views.get_deals, name='recent_deals'),
    url(r'^offers/search/$', product_views.search_deals, name='search_deals'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns.extend(web_1_0_urlpatterns)
