from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from api.barriers.models import Barrier
from api.collaboration.models import TeamMember
from api.collaboration.serializers import BarrierTeamSerializer
from api.user.helpers import get_django_user_by_sso_user_id
from api.user.models import Profile


class BarrierTeamMembersView(generics.ListCreateAPIView):
    """
    Returns the team members for a barrier.
    Read only endpoint, Contributors are added automatically.
    """

    queryset = TeamMember.objects.all()
    serializer_class = BarrierTeamSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk")).order_by(
            "-role", "created_on"
        )

    def perform_create(self, serializer):
        barrier = get_object_or_404(Barrier, pk=self.kwargs.get("pk"))
        user = self.request.data.get("user")
        sso_user_id = user["profile"]["sso_user_id"]
        django_user = get_django_user_by_sso_user_id(sso_user_id)

        members = TeamMember.objects.filter(barrier=barrier, user=django_user).count()
        if members:
            raise ValidationError("Team member already exist.")
        else:
            serializer.save(
                barrier=barrier,
                user=django_user,
                role=TeamMember.CONTRIBUTOR,
                created_by=self.request.user,
            )
            return Response(status=status.HTTP_200_OK, data=serializer.data)


class BarrierTeamMemberDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Returns details of a Barrier team member
    Allows the barrier team member to be deleted (archive)
    Allows the barrier owner to be updated.
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

    def patch(self, request, *args, **kwargs):
        """Only allow to update OWNER members"""
        instance = self.get_object()
        if instance.role == TeamMember.OWNER:
            user_id = self.request.data.get("user")
            user_profile = get_object_or_404(Profile, sso_user_id=user_id)
            instance.user = user_profile.user
            instance.modified_by = self.request.user
            instance.save()
            serializer = BarrierTeamSerializer(instance)
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        else:
            raise PermissionDenied()
