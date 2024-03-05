from django.urls import path
from rest_framework.routers import DefaultRouter

from api.feature_flags.views import UserFeatureFlagView

router = DefaultRouter(trailing_slash=False)


urlpatterns = router.urls + [
    path(
        "feature-flags",
        UserFeatureFlagView.as_view({"get": "list"}),
        name="feature-flags",
    ),
    path(
        "users/<uuid:pk>/feature-flags",
        UserFeatureFlagView.as_view({"get": "list"}),
        name="user-feature-flags",
    ),
]
