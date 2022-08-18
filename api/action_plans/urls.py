from django.urls import path
from rest_framework.routers import DefaultRouter

from api.action_plans.views import (
    ActionPlanMilestoneViewSet,
    ActionPlanStakeholderViewSet,
    ActionPlanTaskViewSet,
    ActionPlanViewSet,
)

app_name = "action_plans"

router = DefaultRouter(trailing_slash=False)

urlpatterns = router.urls + [
    path(
        "barriers/<uuid:barrier>/action_plan",
        ActionPlanViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
            }
        ),
        name="action-plans",
    ),
    path(
        "barriers/<uuid:barrier>/action_plan/milestones",
        ActionPlanMilestoneViewSet.as_view({"post": "create", "get": "list"}),
        name="action-plans-milestones",
    ),
    path(
        "barriers/<uuid:barrier>/action_plan/milestones/<uuid:id>",
        ActionPlanMilestoneViewSet.as_view(
            {
                "put": "update",
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="action-plans-milestones-detail",
    ),
    path(
        "barriers/<uuid:barrier>/action_plan/tasks",
        ActionPlanTaskViewSet.as_view({"post": "create"}),
        name="action-plans-tasks",
    ),
    path(
        "barriers/<uuid:barrier>/action_plan/tasks/<uuid:id>",
        ActionPlanTaskViewSet.as_view(
            {
                "put": "update",
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="action-plans-tasks-detail",
    ),
    path(
        "barriers/<uuid:barrier>/action_plan/stakeholders/",
        ActionPlanStakeholderViewSet.as_view({"post": "create"}),
        name="action-plans-stakeholders",
    ),
    path(
        "barriers/<uuid:barrier>/action_plan/stakeholders/<uuid:id>/",
        ActionPlanStakeholderViewSet.as_view(
            {
                "put": "update",
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="action-plans-stakeholders-detail",
    ),
]
