from django.shortcuts import get_object_or_404, render
from django.contrib.auth import get_user_model

from rest_framework import generics

from api.barriers.models import BarrierInstance
from api.collaboration.models import TeamMember
from api.collaboration.serializers import BarrierTeamSerializer

UserModel = get_user_model()


class BarrierTeamMembersView(generics.ListCreateAPIView):
    """
    Handling Barrier interactions, such as notes
    """

    queryset = TeamMember.objects.all()
    serializer_class = BarrierTeamSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk"))

    def perform_create(self, serializer):
        barrier_obj = get_object_or_404(BarrierInstance, pk=self.kwargs.get("pk"))
        user = self.request.data.get("user")
        try:
            user = UserModel.objects.get(username=user["username"])
        except UserModel.DoesNotExist:
            UserModel.objects.create(
                username=user["username"],
                email=user["email"],
                first_name=user["first_name"],
                lastname=user["lastname"],
            )
            user = UserModel.objects.get(username=user["username"])

        role = self.request.data.get("role", None)

        serializer.save(
            barrier=barrier_obj,
            user=user,
            role=role,
            created_by=self.request.user,
        )
        barrier_obj.save()


class BarrierIneractionDetail(generics.RetrieveDestroyAPIView):
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
        instance.archive(self.request.user)
