from django.urls import path

from api.collaboration.views import (
    BarrierTeamMembersView,
)

urlpatterns = [
    path(
        "barriers/<uuid:pk>/members",
        BarrierTeamMembersView.as_view(),
        name="list-members",
    ),
]
