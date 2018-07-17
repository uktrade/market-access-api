from django.db.models import Manager
from django.db.models.query import QuerySet

from rest_framework import serializers

from api.barriers.models import BarrierInstance, BarrierStatus
from api.metadata.models import BarrierType
from api.metadata.constants import BARRIER_STATUS


class BarrierInstanceSerializer(serializers.ModelSerializer):
    current_status = serializers.SerializerMethodField()
    report_id = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "barrier_type",
            "summary",
            "chance_of_success",
            "chance_of_success_summary",
            "estimated_loss_range",
            "impact_summary",
            "other_companies_affected",
            "has_legal_infringement",
            "wto_infringement",
            "fta_infringement",
            "other_infringement",
            "infringement_summary",
            "reported_on",
            "created_on",
            "report_id",
            "created_by",
            "current_status"
        )

    def get_current_status(self, obj):
        barrier_status = BarrierStatus.objects.filter(barrier=obj).latest("created_on")
        return {
            "status": barrier_status.status,
            "created_on": barrier_status.created_on,
            "created_by": barrier_status.created_by
        }

    def get_report_id(self, obj):
        return obj.report.id