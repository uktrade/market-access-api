from django.contrib.auth import get_user_model
from hawkrest import HawkAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.barriers.models import Barrier
from api.barriers.serializers import DataWorkspaceSerializer
from api.dataset.service import process_request
from api.dataset.pagination import MarketAccessDatasetViewCursorPagination
from api.dataset.table_schemas import DATASET_SCHEMAS
from api.feedback.models import Feedback
from api.feedback.serializers import FeedbackSerializer
from api.user.models import UserActvitiyLog
from api.user.serializers import UserActvitiyLogSerializer, UserSerializer

UserModel = get_user_model()


class SchemaView(generics.RetrieveAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs):
        return Response(DATASET_SCHEMAS)


class LoadView(generics.ListAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        return Response(process_request(request))


class BarrierList(generics.ListAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    pagination_class = MarketAccessDatasetViewCursorPagination

    queryset = (
        Barrier.barriers.all()
        .select_related(
            "priority",
        )
        .prefetch_related(
            "barrier_commodities",
            "categories",
            "economic_assessments",
            "organisations",
            "tags",
            "top_priority_summary",
        )
        .order_by("reported_on")
    )

    serializer_class = DataWorkspaceSerializer


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
