from django.urls import path

from api.commodities.views import CommodityDetail, CommodityList, related_barriers_view

urlpatterns = [
    path("commodities", CommodityList.as_view(), name="commodity-list"),
    path("commodities/<str:code>", CommodityDetail.as_view(), name="commodity-detail"),
    path("commodities/search/", related_barriers_view, name="commodity-search"),
]
