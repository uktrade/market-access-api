from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from api.ping.views import ping
from api.user.views import who_am_i

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    path('ping.xml', ping, name='ping'),
    path('whoami/', who_am_i, name='who_am_i'),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
