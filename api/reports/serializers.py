from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.metadata.constants import STAGE_STATUS
from api.metadata.models import BarrierType
from api.reports.models import Report, ReportStage, Stage


class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStage
        fields = "__all__"


class ReportStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStage
        fields = ("id", "stage", "status", "created_on", "created_by")
        depth = 1


class ReportStageListingField(serializers.RelatedField):
    def to_representation(self, value):
        stage_status_dict = dict(STAGE_STATUS)
        return {
            "stage_code": value.stage.code,
            "stage_desc": value.stage.description,
            "status_id": value.status,
            "status_desc": stage_status_dict[value.status],
        }


class BarrierTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierType
        fields = "__all__"


class ReportSerializer(serializers.ModelSerializer):
    progress = ReportStageListingField(many=True, read_only=True)

    class Meta:
        model = Report
        exclude = ("stages",)
        read_only_fields = ("id", "stages", "progress", "created_on")
        depth = 1
