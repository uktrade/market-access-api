from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

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

    @transaction.atomic()
    def perform_create(self, serializer):
        barrier_obj = get_object_or_404(BarrierInstance, pk=self.kwargs.get("pk"))
        user = self.request.data.get("user")
        sso_user_id = user["profile"]["sso_user_id"]
        try:
            user_profile = Profile.objects.get(sso_user_id=sso_user_id)
            user = user_profile.user
        except Profile.DoesNotExist:
            sso_user = sso.get_user_details_by_id(sso_user_id)
            user = UserModel(
                username=sso_user["email"],
                email=sso_user["email"],
                first_name=sso_user["first_name"],
                last_name=sso_user["last_name"],
            )
            user.save()
            user.profile.sso_user_id = sso_user_id
            user.profile.save()

        role = self.request.data.get("role", None)

        serializer.save(
            barrier=barrier_obj,
            user=user,
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
