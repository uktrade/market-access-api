from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.user.serializers import WhoAmISerializer
from api.core.auth import IsMAServer, IsMAUser

PERMISSION_CLASSES = (IsAuthenticated)


@api_view()
@permission_classes([])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    # permission_classes = PERMISSION_CLASSES
    serializer = WhoAmISerializer(request.user)

    return Response(data=serializer.data)
