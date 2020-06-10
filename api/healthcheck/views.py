import time

from django.conf import settings
from django.views.generic import TemplateView

from hawkrest import HawkAuthentication

from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from .checks import db_check

HAWK = [HawkAuthentication] if getattr(settings, "HAWK_ENABLED", True) else []
AUTH = [IsAuthenticated] if getattr(settings, "HAWK_ENABLED", True) else []


@authentication_classes(HAWK)
@permission_classes(AUTH)
class HealthCheckView(TemplateView):
    template_name = "healthcheck.html"

    def get_context_data(self, **kwargs):
        """ Adds status and response time to response context """
        context = super().get_context_data(**kwargs)
        context["status"] = db_check()
        # nearest approximation of a response time
        context["response_time"] = time.time() - self.request.start_time
        return context
