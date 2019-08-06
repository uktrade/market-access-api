from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api.barriers.models import BarrierInstance
from api.collaboration.models import TeamMember
from api.collaboration.serializers import BarrierTeamSerializer
from api.user.models import Profile
from api.user.staff_sso import StaffSSO

UserModel = get_user_model()
sso = StaffSSO()


class BarrierTeamMembersView(generics.ListCreateAPIView):
    """
    Handling Barrier interactions, such as notes
    """

    queryset = TeamMember.objects.all()
    serializer_class = BarrierTeamSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk")).order_by("created_on")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        barrier_obj = get_object_or_404(BarrierInstance, pk=self.kwargs.get("pk"))
        user = self.request.data.get("user")
        sso_user_id = user["profile"]["sso_user_id"]
        user_profile = get_object_or_404(Profile, sso_user_id=sso_user_id)
        role = self.request.data.get("role", None)

        barrier_member_count = TeamMember.objects.filter(
            Q(barrier=barrier_obj) & Q(user=user_profile.user)
        ).count()
        if barrier_member_count > 0:
            raise serializers.ValidationError("member already exists")

        serializer.save(
            barrier=barrier_obj,
            user=user_profile.user,
            role=role,
            created_by=self.request.user,
        )
        barrier_obj.save()


class BarrierTeamMemberDetail(generics.RetrieveDestroyAPIView):
    """
    Return details of a Barrier team member
    Allows the barrier team member to be deleted (archive)
    """

    lookup_field = "pk"
    queryset = TeamMember.objects.all()
    serializer_class = BarrierTeamSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_destroy(self, instance):
        if instance.default:
            raise PermissionDenied()

        instance.archive(self.request.user)
