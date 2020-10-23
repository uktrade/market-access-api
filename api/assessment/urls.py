from django.urls import path

from api.assessment.views import (
    BarrierAssessmentDetail,
    BarrierAssessmentHistory,
    ResolvabilityAssessmentList,
)

urlpatterns = [
    path(
        "barriers/<uuid:pk>/assessment",
        BarrierAssessmentDetail.as_view(),
        name="get-assessment",
    ),
    path(
        "resolvability-assessments",
        ResolvabilityAssessmentList.as_view(),
        name="resolvability-assessments",
    ),
    path(
        "barriers/<uuid:pk>/assessment_history",
        BarrierAssessmentHistory.as_view(),
        name="assessment-history",
    ),
]
