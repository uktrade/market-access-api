import time

from hawkrest import HawkAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from api.core.permissions import IsAuthenticated

from .checks import db_check


class HealthCheckView(GenericAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)
    schema = None

    def get(self, request):
        data = {"duration": time.time() - request.start_time, "status": db_check()}

        return Response(data=data)
