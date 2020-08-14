from django.urls import path

from .views import BarrierList

app_name = "dataset"

urlpatterns = [
    path("dataset/v1/barriers", BarrierList.as_view(), name="barrier-list"),
]
