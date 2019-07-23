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
        try:
            user = UserModel.objects.get(username=self.request.data.get("user"))
        except UserModel.DoesNotExist:
            
        role = self.request.data.get("role", None)

        serializer.save(
            barrier=barrier_obj,
            user=user,
            role=role,
            created_by=self.request.user,
        )
        barrier_obj.save()
