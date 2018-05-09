from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from api.ping.views import ping

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    path('ping.xml', ping, name='ping'),
]
