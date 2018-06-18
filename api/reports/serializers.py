from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from api.reports.models import Report, ReportStage, Stage


class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStage
        fields = '__all__'


class ReportStageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportStage
        fields = (
            'id',
            'stage',
            'status',
            'created_on',
            'created_by'
        )
        depth = 1


class ReportSerializer(serializers.ModelSerializer):
    # stages = ReportStageSerializer(many=True, read_only=True)

    class Meta:
        model = Report
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
            'name',
            'summary',
            'status',
            'created_on',
            'created_by',
            'stages'
        )
        read_only_fields = (
            'id',
            'created_on',
        )
        depth = 1
