from django.urls import path

from api.collaboration.views import (
    BarrierTeamMembersView,
    BarrierTeamMemberDetail
)

urlpatterns = [
    path(
        "barriers/<uuid:pk>/members",
        BarrierTeamMembersView.as_view(),
        name="list-members",
    ),
    path(
        "barriers/members/<int:pk>",
        BarrierTeamMemberDetail.as_view(),
        name="get-member",
    ),
]
