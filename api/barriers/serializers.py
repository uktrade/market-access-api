from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from api.barriers.models import Barrier, BarrierReportStage, ReportStage
from api.barriers.company import Company


class ReportStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStage
        fields = '__all__'


class BarrierReportStageSerializer(serializers.ModelSerializer):

    class Meta:
        model = BarrierReportStage
        fields = (
            'id',
            'stage',
            'status',
            'created_on',
            'created_by'
        )
        depth = 1


class BarrierSerializer(serializers.ModelSerializer):
    report_stages = BarrierReportStageSerializer(many=True, read_only=True)

    class Meta:
        model = Barrier
        fields = (
            'id',
            'problem_status',
            'is_emergency',
            'company_id',
            'company_name',
            'contact_id',
            'product',
            'commodity_codes',
            'export_country',
            'problem_description',
            'problem_impact',
            'estimated_loss_range',
            'other_companies_affected',
            'govt_response_requester',
            'is_confidential',
            'sensitivity_summary',
            'can_publish',
            'barrier_name',
            'barrier_summary',
            'status',
            'created_on',
            'created_by',
            'report_stages'
        )
        read_only_fields = (
            'id',
            'created_on',
        )
        depth = 1


class BarrierDetailSerializer(serializers.ModelSerializer):
    report_stages = ReportStageSerializer(many=True, read_only=True)

    class Meta:
        model = Barrier
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_on',
        )
        depth = 1


class BarrierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = '__all__'
        depth = 1
