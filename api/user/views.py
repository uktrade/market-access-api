from rest_framework import status

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.user.models import Profile
from api.user.serializers import WhoAmISerializer

TOKEN_SESSION_KEY = '_authbroker_token'

@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    token = request.session.get(TOKEN_SESSION_KEY, None)
    context = {"token": token}
    serializer = WhoAmISerializer(request.user, context=context)

    if request.method == 'PATCH':
        req_profile = request.data.get("user_profile", None)
        if req_profile:
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                Profile.objects.create(user=request.user)

            request.user.profile.user_profile = req_profile
            request.user.profile.save()
            request.user.save()

    if request.method == 'POST':
        return Response(data=request.data)
    return Response(data=serializer.data)
