from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.user.models import Profile
from api.user.serializers import WhoAmISerializer, UserSerializer
from api.user.staff_sso import StaffSSO

TOKEN_SESSION_KEY = '_authbroker_token'
UserModel = get_user_model()
sso = StaffSSO()


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
        try:
            user_profile = Profile.objects.get(sso_user_id=sso_user_id)
            user = user_profile.user
        except Profile.DoesNotExist:
            sso_user = sso.get_user_details_by_id(sso_user_id)
            try:
                user = UserModel.objects.get(username=sso_user["email"])
                user.email = sso_user["email"]
                user.first_name = sso_user["first_name"]
                user.last_name = sso_user["last_name"]
                user.save()
            except UserModel.DoesNotExist:
                user = UserModel(
                    username=sso_user["email"],
                    email=sso_user["email"],
                    first_name=sso_user["first_name"],
                    last_name=sso_user["last_name"],
                )
                user.save()
            user.profile.sso_user_id = sso_user_id
            user.profile.save()
        return user
