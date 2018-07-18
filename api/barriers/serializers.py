from django.db.models import Manager
from django.db.models.query import QuerySet

from rest_framework import serializers

from api.barriers.models import (
    BarrierContributor,
    BarrierInstance, 
    BarrierStatus
)
from api.metadata.models import BarrierType
from api.metadata.constants import BARRIER_STATUS


class BarrierListSerializer(serializers.ModelSerializer):
    current_status = serializers.SerializerMethodField()
    report_id = serializers.SerializerMethodField()
    barrier_title = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    export_country = serializers.SerializerMethodField()
    support_type = serializers.SerializerMethodField()
    contributor_count = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "report_id",
            "reported_on",
            "barrier_title",
            "company",
            "export_country",
            "support_type",
            "contributor_count",
            "current_status"
        )

    def get_report_id(self, obj):
        return obj.report.id

    def get_current_status(self, obj):
        barrier_status = BarrierStatus.objects.filter(barrier=obj).latest("created_on")
        return {
            "status": barrier_status.status,
            "created_on": barrier_status.created_on,
            "created_by": barrier_status.created_by
        }

    def get_barrier_title(self, obj):
        return obj.report.barrier_title
    
    def get_company(self, obj):
        return {
            "id": obj.report.company_id,
            "name": obj.report.company_name,
            "sector_name": obj.report.company_sector_name
        }
        
    def get_export_country(self, obj):
        return obj.report.export_country

    def get_support_type(self, obj):
        return obj.report.support_type
    
    def get_contributor_count(self, obj):
        barrier_contributors_count = BarrierContributor.objects.filter(barrier=obj, is_active=True).count()
        return barrier_contributors_count


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
            "report_id",
            "reported_on",
            "created_on",
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