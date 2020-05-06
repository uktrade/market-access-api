from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api.user.models import Profile
from api.user.models import get_my_barriers_saved_search, get_team_barriers_saved_search
from api.user.serializers import WhoAmISerializer, UserSerializer, SavedSearchSerializer
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
            email = sso_user.get("email")
            contact_email = sso_user.get("contact_email") or email
            first_name = sso_user.get("first_name")
            last_name = sso_user.get("last_name")
            try:
                user = UserModel.objects.get(username=email)
                user.email = contact_email
                user.first_name = first_name
                user.last_name = last_name
                user.save()
            except UserModel.DoesNotExist:
                user = UserModel(
                    username=email,
                    email=contact_email,
                    first_name=first_name,
                    last_name=last_name,
                )
                user.save()
            user.profile.sso_user_id = sso_user_id
            user.profile.save()
        return user


class SavedSearchList(generics.ListCreateAPIView):
    serializer_class = SavedSearchSerializer

    def get_queryset(self):
        return self.request.user.saved_searches.all()


class SavedSearchDetail(generics.RetrieveUpdateAPIView):
    serializer_class = SavedSearchSerializer

    def get_object(self):
        if self.kwargs.get("id") == "my-barriers":
            return get_my_barriers_saved_search(self.request.user)

        if self.kwargs.get("id") == "team-barriers":
            return get_team_barriers_saved_search(self.request.user)

        return super().get_object()

    def get_queryset(self):
        return self.request.user.saved_searches.all()
