from django.urls import path

from api.assessment.views import (
    EconomicAssessmentDetail,
    EconomicAssessmentList,
    ResolvabilityAssessmentDetail,
    ResolvabilityAssessmentList,
    StrategicAssessmentDetail,
    StrategicAssessmentList,
)

urlpatterns = [
    path(
        "economic-assessments",
        EconomicAssessmentList.as_view(),
        name="economic-assessment-list",
    ),
    path(
        "economic-assessments/<int:pk>",
        EconomicAssessmentDetail.as_view(),
        name="economic-assessment-detail",
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
]
