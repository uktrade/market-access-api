from django.contrib.auth import get_user_model

from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.user.helpers import get_django_user_by_sso_user_id
from api.user.models import Profile
from api.user.serializers import WhoAmISerializer, UserSerializer

UserModel = get_user_model()


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    token = request.auth.token
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


class UserDetail(generics.RetrieveDestroyAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        sso_user_id = self.kwargs.get("sso_user_id")
        return get_django_user_by_sso_user_id(sso_user_id)
