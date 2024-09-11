from datetime import datetime
from dateutil.relativedelta import relativedelta
from hawkrest import HawkAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import get_user_model

from api.barriers.models import Barrier
from api.barriers.serializers import DataWorkspaceSerializer
from api.dataset.pagination import MarketAccessDatasetViewCursorPagination
from api.feedback.models import Feedback
from api.feedback.serializers import FeedbackSerializer
from api.user.models import UserActvitiyLog
from api.user.serializers import UserActvitiyLogSerializer, UsersSerializer

UserModel = get_user_model()


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


class UsersList(generics.ListAPIView):
    # authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        login_cutoff = datetime.now() - relativedelta(months=6)
        return (
            UserModel.objects.all()
            .filter(last_login__gte=login_cutoff)
            .order_by("-last_login")
        )

    serializer_class = UsersSerializer
