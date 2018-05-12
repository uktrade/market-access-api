from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from api.ping.views import ping
from api.user.views import who_am_i

urlpatterns = [
    path('ping.xml', ping, name='ping'),
    path('whoami/', who_am_i, name='who_am_i'),
]
