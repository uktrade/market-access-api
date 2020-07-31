from django.urls import path

from api.commodities.views import CommodityDetail, CommodityList


urlpatterns = [
    path("commodities", CommodityList.as_view(), name="commodity-list"),
    path("commodities/<str:code>", CommodityDetail.as_view(), name="commodity-detail"),
]
