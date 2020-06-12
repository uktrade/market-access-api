import time

from django.conf import settings
from hawkrest import HawkAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.core.permissions import IsAuthenticated
from .checks import db_check


class HealthCheckView(GenericAPIView):
    if settings.HAWK_ENABLED:
        authentication_classes = (HawkAuthentication,)
        permission_classes = (IsAuthenticated,)
    else:
        authentication_classes = ()
        permission_classes = ()

    def get(self, request):
        data = {
            "duration": time.time() - request.start_time,
            "status": db_check()
        }

        return Response(data=data)
