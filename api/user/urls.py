from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    GroupDetail,
    GroupList,
    ProfileDetail,
    SavedSearchDetail,
    SavedSearchList,
    UserActivityLogList,
    UserDetail,
    UserList,
)

router = DefaultRouter(trailing_slash=False)

urlpatterns = router.urls + [
    path("saved-searches", SavedSearchList.as_view(), name="saved-search-list"),
    path(
        "saved-searches/<uuid:pk>",
        SavedSearchDetail.as_view(),
        name="saved-search-detail",
    ),
    re_path(
        "saved-searches/(?P<id>my-barriers)",
        SavedSearchDetail.as_view(),
        name="my-barriers-saved-search",
    ),
    re_path(
        "saved-searches/(?P<id>team-barriers)",
        SavedSearchDetail.as_view(),
        name="team-barriers-saved-search",
    ),
    path("groups", GroupList.as_view(), name="group-list"),
    path("groups/<int:pk>", GroupDetail.as_view(), name="group-detail"),
    path("users/<int:pk>", UserDetail.as_view(), name="get-user"),
    path("users/<uuid:sso_user_id>", UserDetail.as_view(), name="get-user"),
    path("users/profile/<int:pk>", ProfileDetail.as_view(), name="get-profile"),
    path("users", UserList.as_view(), name="user-list"),
    path("user_activity_log", UserActivityLogList.as_view(), name="user-activity-log"),
]
