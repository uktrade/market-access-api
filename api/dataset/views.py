from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from hawkrest import HawkAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.barriers.models import Barrier, EstimatedResolutionDateRequest
from api.barriers.serializers import DataWorkspaceSerializer
from api.dataset.pagination import MarketAccessDatasetViewCursorPagination
from api.dataset.service import get_barrier_history
from api.feedback.models import Feedback
from api.feedback.serializers import FeedbackSerializer
from api.user.models import UserActvitiyLog
from api.user.serializers import UserActvitiyLogSerializer, UserSerializer

UserModel = get_user_model()


class BarrierList(generics.ListAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    pagination_class = MarketAccessDatasetViewCursorPagination

    queryset = (
        Barrier.barriers.all()
        .select_related("priority", "preliminary_assessment")
        .prefetch_related(
            "barrier_commodities",
            "economic_assessments",
            "organisations",
            "tags",
            "top_priority_summary",
            Prefetch(
                "estimated_resolution_date_request",
                queryset=EstimatedResolutionDateRequest.objects.filter(
                    status="NEEDS_REVIEW"
                ),
            ),
        )
        .order_by("reported_on")
    )

    serializer_class = DataWorkspaceSerializer


class BarrierHistoryStreamView(generics.ListAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        return Response(get_barrier_history(request))


class FeedbackDataWorkspaceListView(generics.ListAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer


class UserActivityLogView(generics.ListAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = UserActvitiyLog.objects.all()
    serializer_class = UserActvitiyLogSerializer


class UserList(generics.ListAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return UserModel.objects.values(
            "id", "email", "first_name", "last_name", "last_login"
        ).order_by("id")

    serializer_class = UserSerializer
