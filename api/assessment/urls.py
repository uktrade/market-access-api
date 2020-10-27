from django.urls import path

from api.assessment.views import (
    BarrierAssessmentDetail,
    BarrierAssessmentHistory,
    ResolvabilityAssessmentDetail,
    ResolvabilityAssessmentList,
    StrategicAssessmentDetail,
    StrategicAssessmentList,
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
        name="resolvability-assessment-list",
    ),
    path(
        "resolvability-assessments/<uuid:pk>",
        ResolvabilityAssessmentDetail.as_view(),
        name="resolvability-assessment-detail",
    ),
    path(
        "strategic-assessments",
        StrategicAssessmentList.as_view(),
        name="strategic-assessment-list",
    ),
    path(
        "strategic-assessments/<uuid:pk>",
        StrategicAssessmentDetail.as_view(),
        name="strategic-assessment-detail",
    ),
    path(
        "barriers/<uuid:pk>/assessment_history",
        BarrierAssessmentHistory.as_view(),
        name="assessment-history",
    ),
]
