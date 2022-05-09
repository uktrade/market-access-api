from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import F
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from api.user.helpers import get_django_user_by_sso_user_id
from api.user.models import (
    Profile,
    get_my_barriers_saved_search,
    get_team_barriers_saved_search,
)
from api.user.serializers import (
    GroupSerializer,
    SavedSearchSerializer,
    UserDetailSerializer,
    UserListSerializer,
    WhoAmISerializer,
)

UserModel = get_user_model()


@api_view(["GET", "POST", "PATCH"])
@permission_classes([])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    try:
        token = request.auth.token
    except AttributeError:
        print(request.auth)
        return HttpResponse("Unauthorized", status=HTTPStatus.UNAUTHORIZED)

    context = {"token": token}
    serializer = WhoAmISerializer(request.user, context=context)

    if request.method == "PATCH":
        req_profile = request.data.get("user_profile", None)
        if req_profile:
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                Profile.objects.create(user=request.user)

            request.user.profile.user_profile = req_profile
            request.user.profile.save()
            request.user.save()

    if request.method == "POST":
        return Response(data=request.data)
    return Response(data=serializer.data)


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserDetailSerializer

    def get_object(self):
        sso_user_id = self.kwargs.get("sso_user_id")
        if sso_user_id:
            return get_django_user_by_sso_user_id(sso_user_id)
        return super().get_object()


class SavedSearchList(generics.ListCreateAPIView):
    serializer_class = SavedSearchSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]

    def get_queryset(self):
        return self.request.user.saved_searches.all()


class SavedSearchDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavedSearchSerializer

    def get_object(self):
        if self.kwargs.get("id") == "my-barriers":
            return get_my_barriers_saved_search(self.request.user)

        if self.kwargs.get("id") == "team-barriers":
            return get_team_barriers_saved_search(self.request.user)

        return super().get_object()

    def get_queryset(self):
        return self.request.user.saved_searches.all()


class GroupList(generics.ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupDetail(generics.RetrieveAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class UserList(generics.ListAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserListSerializer
    filter_backends = [OrderingFilter, SearchFilter, DjangoFilterBackend]
    ordering_fields = ("last_name", "first_name", "email", "role")
    ordering = ("first_name", "last_name", "email", "role")
    search_fields = ("first_name", "last_name", "email")
    filterset_fields = [
        "groups__id",
    ]

    def list(self, request, *args, **kwargs):
        self.paginator.default_limit = 10
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().annotate(role=F("groups__name"))
