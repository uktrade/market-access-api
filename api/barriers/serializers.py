from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from api.barriers.models import Barrier, BarrierReportStage, ReportStage
from api.barriers.company import Company


class ReportStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStage
        fields = '__all__'


# class BarrierReportStageSerializer(serializers.ModelSerializer):
#     stage = serializers.StringRelatedField(many=True, read_only=True)

#     class Meta:
#         model = BarrierReportStage
#         fields = ('stage', 'status')


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


class BarrierReportStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierReportStage
        fields = '__all__'
