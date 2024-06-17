from django.urls import path

from .views import pingdom

urlpatterns = [
    path("pingdom/ping.xml", pingdom, name="pingdom"),
]
