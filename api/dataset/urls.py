from django.urls import path

from .views import BarrierList, FeedbackDataWorkspaceListView

app_name = "dataset"

urlpatterns = [
    path("dataset/v1/barriers", BarrierList.as_view(), name="barrier-list"),
    path(
        "dataset/v1/feedback",
        FeedbackDataWorkspaceListView.as_view(),
        name="feedback-list",
    ),
]
