from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from api.barriers.views import (
    BarrierActivity,
    BarrierDetail,
    BarrierFullHistory,
    BarrierHibernate,
    BarrierList,
    BarrierNextStepItemViewSet,
    BarrierOpenActionRequired,
    BarrierOpenInProgress,
    BarrierPrioritySummaryViewSet,
    BarrierProgressUpdateViewSet,
    BarrierReportDetail,
    BarrierReportList,
    BarrierReportSubmit,
    BarrierResolveInFull,
    BarrierResolveInPart,
    BarrierStatusChangeUnknown,
    EstimatedResolutionDateRequestApproveView,
    EstimatedResolutionDateRequestRejectView,
    EstimatedResolutionDateRequestView,
    ProgrammeFundProgressUpdateViewSet,
    PublicBarrierActivity,
    PublicBarrierViewSet,
    barrier_count,
)

app_name = "barriers"

router = DefaultRouter(trailing_slash=False)
# Important Notice: Public barriers should only be used within Market Access Service exclusively!
router.register(r"public-barriers", PublicBarrierViewSet, basename="public-barriers")


urlpatterns = router.urls + [
    path("barriers", BarrierList.as_view(), name="list-barriers"),
    re_path(
        "barriers/(?P<code>[A-Z]-[0-9]{2}-[A-Z0-9]{3})",
        BarrierDetail.as_view(),
        name="barrier_detail_code",
    ),
    path("barriers/<uuid:pk>", BarrierDetail.as_view(), name="get-barrier"),
    path(
        "barriers/<uuid:barrier_id>/estimated-resolution-date-request",
        EstimatedResolutionDateRequestView.as_view(),
        name="estimated-resolution-date-request",
    ),
    path(
        "barriers/<uuid:barrier_id>/estimated-resolution-date-request/approve",
        EstimatedResolutionDateRequestApproveView.as_view(),
        name="estimated-resolution-date-request-approve",
    ),
    path(
        "barriers/<uuid:barrier_id>/estimated-resolution-date-request/reject",
        EstimatedResolutionDateRequestRejectView.as_view(),
        name="estimated-resolution-date-request-reject",
    ),
    path("barriers/<uuid:pk>/activity", BarrierActivity.as_view(), name="activity"),
    path(
        "barriers/<uuid:pk>/full_history",
        BarrierFullHistory.as_view(),
        name="history",
    ),
    path(
        "barriers/<uuid:pk>/hibernate",
        BarrierHibernate.as_view(),
        name="hibernate-barrier",
    ),
    path(
        "barriers/<uuid:pk>/open-action_required",
        BarrierOpenActionRequired.as_view(),
        name="open-action",
    ),
    path(
        "barriers/<uuid:barrier_pk>/top_100_progress_updates",
        BarrierProgressUpdateViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="top_100_progress_updates",
    ),
    path(
        "barriers/<uuid:barrier_pk>/top_100_progress_updates/<uuid:pk>",
        BarrierProgressUpdateViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="top_100_progress_updates_detail",
    ),
    path(
        "barriers/<uuid:barrier_pk>/next_steps_items",
        BarrierNextStepItemViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="next_steps_items",
    ),
    path(
        "barriers/<uuid:barrier_pk>/next_steps_items/<uuid:pk>",
        BarrierNextStepItemViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="next_steps_items_detail",
    ),
    path(
        "barriers/<uuid:barrier_pk>/top_priority_summary",
        BarrierPrioritySummaryViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="top_priority_summary",
    ),
    path(
        "barriers/<uuid:barrier_pk>/top_priority_summary/<uuid:pk>",
        BarrierPrioritySummaryViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="top_priority_summary_detail",
    ),
    path(
        "barriers/<uuid:barrier_pk>/programme_fund_progress_updates",
        ProgrammeFundProgressUpdateViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="programme_fund_progress_updates",
    ),
    path(
        "barriers/<uuid:barrier_pk>/programme_fund_progress_updates/<uuid:pk>",
        ProgrammeFundProgressUpdateViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="programme_fund_progress_updates_detail",
    ),
    path(
        "barriers/<uuid:pk>/open-in-progress",
        BarrierOpenInProgress.as_view(),
        name="open-in-progress",
    ),
    path(
        "barriers/<uuid:pk>/resolve-in-full",
        BarrierResolveInFull.as_view(),
        name="resolve-in-full",
    ),
    path(
        "barriers/<uuid:pk>/resolve-in-part",
        BarrierResolveInPart.as_view(),
        name="resolve-in-part",
    ),
    path(
        "barriers/<uuid:pk>/unknown",
        BarrierStatusChangeUnknown.as_view(),
        name="unknown-barrier",
    ),
    path("counts", barrier_count, name="barrier-count"),
    path("reports", BarrierReportList.as_view(), name="list-reports"),
    path("reports/<uuid:pk>", BarrierReportDetail.as_view(), name="get-report"),
    path(
        "reports/<uuid:pk>/submit", BarrierReportSubmit.as_view(), name="submit-report"
    ),
    path(
        "public-barriers/<uuid:pk>/activity",
        PublicBarrierActivity.as_view(),
        name="public-activity",
    ),
]
