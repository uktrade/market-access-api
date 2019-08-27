from django.urls import path

from api.assessment.views import (
    BarrierAssessmentDetail,
    BarrierAssessmentHistory,
)

urlpatterns = [
    path(
        "barriers/<uuid:pk>/assessment",
        BarrierAssessmentDetail.as_view(),
        name="get-assessment",
    ),
    path(
        "barriers/<uuid:pk>/assessment_history",
        BarrierAssessmentHistory.as_view(),
        name="assessment-history",
    ),
]
