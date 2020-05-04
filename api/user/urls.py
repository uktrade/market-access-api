from django.urls import path

from .views import SavedSearchDetail, SavedSearchList


urlpatterns = [
    path("saved-searches", SavedSearchList.as_view(), name="saved-search-list"),
    path("saved-searches/<uuid:pk>", SavedSearchDetail.as_view(), name="saved-search-detail"),
]
