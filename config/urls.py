from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view

from api.action_plans.urls import urlpatterns as action_plans_urls
from api.assessment.urls import urlpatterns as assessment_urls
from api.barrier_downloads.urls import urlpatterns as barrier_download_urls
from api.barriers.urls import urlpatterns as barrier_urls
from api.collaboration.urls import urlpatterns as team_urls
from api.commodities.urls import urlpatterns as commodities_urls
from api.core.views import admin_override
from api.dashboard.urls import urlpatterns as dashboard_urls
from api.feedback import urls as feedback_urls
from api.interactions.urls import urlpatterns as interaction_urls
from api.metadata.views import MetadataView
from api.pingdom.urls import urlpatterns as pingdom_urls
from api.related_barriers.urls import urlpatterns as related_barriers_urls
from api.user.urls import urlpatterns as user_urls
from api.user.views import who_am_i

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
        path("feedback/", include(feedback_urls, namespace="feedback")),
        path("whoami", who_am_i, name="who_am_i"),
        path("metadata", MetadataView.as_view(), name="metadata"),
        path("", include("api.dataset.urls", namespace="dataset")),
    ]
    + action_plans_urls
    + assessment_urls
    + barrier_download_urls
    + barrier_urls
    + commodities_urls
    + dashboard_urls
    + interaction_urls
    + pingdom_urls
    + related_barriers_urls
    + team_urls
    + user_urls
)

# Add endpoints for documentation on non-prod environments
if settings.DJANGO_ENV in ["local", "dev", "uat"]:
    urlpatterns += [
        path(
            "openapi",
            get_schema_view(
                title="Digital Market Access Barriers",
                description="API for Digital Market Access",
                version="1.0.0",
            ),
            name="openapi-schema",
        ),
        # Route TemplateView to serve the ReDoc template.
        #   * Provide `extra_context` with view name of `SchemaView`.
        path(
            "redoc/",
            TemplateView.as_view(
                template_name="redoc.html",
                extra_context={"schema_url": "openapi-schema"},
            ),
            name="redoc",
        ),
        path(
            "swagger-ui/",
            TemplateView.as_view(
                template_name="swagger-ui.html",
                extra_context={"schema_url": "openapi-schema"},
            ),
            name="swagger-ui",
        ),
    ]
