from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.user.serializers import WhoAmISerializer


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    serializer = WhoAmISerializer(request.user)

    if request.method == 'PATCH':
        req_profile = request.data.get("user_profile", None)
        if req_profile:
            if request.user.profile:
                request.user.profile.user_profile = req_profile
                request.user.profile.save()
                request.user.save()

    if request.method == 'POST':
        return Response(data=request.data)
    return Response(data=serializer.data)
