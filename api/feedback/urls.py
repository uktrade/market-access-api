from django.urls import path

from .views import AddFeedbackViewSet

app_name = "feedback"


urlpatterns = [
    path(
        "",
        AddFeedbackViewSet.as_view(
            {
                "post": "create",
            }
        ),
        name="add",
    ),
    path(
        "<int:pk>/",
        AddFeedbackViewSet.as_view(
            {
                "put": "update",
                "patch": "partial_update",
            }
        ),
        name="update",
    ),
]
