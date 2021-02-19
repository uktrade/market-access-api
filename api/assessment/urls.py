from django.urls import path

from api.assessment.views import (
    EconomicAssessmentDetail,
    EconomicAssessmentList,
    EconomicImpactAssessmentDetail,
    EconomicImpactAssessmentList,
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
        "economic-impact-assessments",
        EconomicImpactAssessmentList.as_view(),
        name="economic-impact-assessment-list",
    ),
    path(
        "economic-impact-assessments/<uuid:pk>",
        EconomicImpactAssessmentDetail.as_view(),
        name="economic-impact-assessment-detail",
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
