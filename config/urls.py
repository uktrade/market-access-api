from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from api.action_plans.urls import urlpatterns as action_plans_urls
from api.assessment.urls import urlpatterns as assessment_urls
from api.barriers.urls import urlpatterns as barrier_urls
from api.collaboration.urls import urlpatterns as team_urls
from api.commodities.urls import urlpatterns as commodities_urls
from api.core.views import admin_override
from api.interactions.urls import urlpatterns as interaction_urls
from api.metadata.views import MetadataView
from api.user.urls import urlpatterns as user_urls
from api.user.views import UserDetail, who_am_i

urlpatterns = []

# Allow regular login to admin panel for local development
if settings.DJANGO_ENV != "local":
    urlpatterns += [
        path("admin/login/", admin_override, name="override"),
    ]

urlpatterns += (
    [
        path("admin/", admin.site.urls),
        path("auth/", include("authbroker_client.urls", namespace="authbroker")),
        path("", include("api.healthcheck.urls", namespace="healthcheck")),
        path("whoami", who_am_i, name="who_am_i"),
        path("users/<int:pk>", UserDetail.as_view(), name="get-user"),
        path("users/<uuid:sso_user_id>", UserDetail.as_view(), name="get-user"),
        path("metadata", MetadataView.as_view(), name="metadata"),
        path("", include("api.dataset.urls", namespace="dataset")),
    ]
    + barrier_urls
    + commodities_urls
    + interaction_urls
    + team_urls
    + assessment_urls
    + user_urls
    + action_plans_urls
)
