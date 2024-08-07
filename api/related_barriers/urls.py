from django.urls import path
from rest_framework.routers import DefaultRouter

from api.related_barriers.views import related_barriers, related_barriers_search

app_name = "related_barriers"

router = DefaultRouter(trailing_slash=False)


urlpatterns = router.urls + [
    path(
        "barriers/<uuid:pk>/related-barriers", related_barriers, name="related-barriers"
    ),
    path(
        "related-barriers", related_barriers_search, name="related-barriers-search"
    ),
]
