from django.urls import path
from feedback.views import FeedbackDataWorkspaceListView
from rest_framework.routers import DefaultRouter

app_name = "feedback"

router = DefaultRouter(trailing_slash=False)

urlpatterns = router.urls + [
    path(
        "/feedback-export",
        FeedbackDataWorkspaceListView.as_view(),
        name="list-feedback",
    ),
]
