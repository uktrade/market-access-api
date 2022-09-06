from django.urls import path

from .views import AddFeedbackViewSet

app_name = "feedback"


urlpatterns = [
    path(
        "",
        AddFeedbackViewSet.as_view({"post": "create"}),
        name="add",
    ),
]
