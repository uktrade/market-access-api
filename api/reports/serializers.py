from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers

from api.reports.models import Report, ReportStage, Stage
from api.metadata.constants import STAGE_STATUS


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


class ReportStageListingField(serializers.RelatedField):
    def to_representation(self, value):
        stage_status_dict = dict(STAGE_STATUS)
        return {
            'stage_code': value.stage.code,
            'stage_desc': value.stage.description,
            'status_id': value.status,
            'status_desc': stage_status_dict[value.status]
        }


class ReportSerializer(serializers.ModelSerializer):
    progress = ReportStageListingField(many=True, read_only=True)

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
            'progress'
        )
        read_only_fields = (
            'id',
            'stages',
            'progress',
            'created_on',
        )
        depth = 1
