from django.urls import path

from api.dataset.views import BarrierList, FeedbackDataWorkspaceListView, UserList, SchemaView, LoadView
from api.user.views import UserActivityLogList

app_name = "dataset"

urlpatterns = [
    path("dataset/schema", SchemaView.as_view(), name="dataset-schema"),
    path("dataset/load", LoadView.as_view(), name="dataset-load"),
    path("dataset/v1/barriers", BarrierList.as_view(), name="barrier-list"),
    path(
        "dataset/v1/feedback",
        FeedbackDataWorkspaceListView.as_view(),
        name="feedback-list",
    ),
    path(
        "dataset/v1/user_activity_log",
        UserActivityLogList.as_view(),
        name="user-activity-log",
    ),
    path(
        "dataset/v1/users",
        UserList.as_view(),
        name="user-list",
    ),
]
