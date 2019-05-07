from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics
from rest_framework.response import Response

from api.user.serializers import WhoAmISerializer


@api_view(['GET', 'POST'])
@permission_classes([])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    serializer = WhoAmISerializer(request.user)

    if request.method == 'POST':
        return Response(data=request.data)
    return Response(data=serializer.data)
