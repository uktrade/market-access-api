from django.urls import path, re_path

from .views import SavedSearchDetail, SavedSearchList


urlpatterns = [
    path("saved-searches", SavedSearchList.as_view(), name="saved-search-list"),
    path("saved-searches/<uuid:pk>", SavedSearchDetail.as_view(), name="saved-search-detail"),
    re_path("saved-searches/(?P<id>my-barriers)", SavedSearchDetail.as_view(), name="my-barriers-saved-search"),
    re_path("saved-searches/(?P<id>team-barriers)", SavedSearchDetail.as_view(), name="team-barriers-saved-search"),
]
