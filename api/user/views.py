from rest_framework import status

from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics
from rest_framework.response import Response

from api.user.serializers import WhoAmISerializer

TOKEN_SESSION_KEY = '_authbroker_token'

@api_view(['GET', 'POST'])
@permission_classes([])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    token = request.session.get(TOKEN_SESSION_KEY, None)
    context = {"token": token}
    serializer = WhoAmISerializer(request.user, context=context)

    if request.method == 'POST':
        return Response(data=request.data)
    return Response(data=serializer.data)
