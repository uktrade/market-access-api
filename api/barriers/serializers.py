from rest_framework import serializers

from api.barriers.models import Barrier, BarrierReportStage, ReportStage
from api.barriers.company import Company


class ReportStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStage
        fields = '__all__'


class BarrierReportStageSerializer(serializers.ModelSerializer):
    stage = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = BarrierReportStage
        fields = ('stage', 'status')


class BarrierDetailSerializer(serializers.ModelSerializer):
    report_stages = ReportStageSerializer(many=True, read_only=True)

    class Meta:
        model = Barrier
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_on',
            'created_by',
        )
        depth = 1


class BarrierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_on',
            'created_by',
        )
        created_by = serializers.HiddenField(
            default=serializers.CurrentUserDefault()
        )
        depth = 1

    def to_representation(self, obj):
        return {
            'id': obj.id,
            'company_id': obj.company_id,
            'company_name': obj.company_name,
            'status': obj.status,
            'problem_status': obj.problem_status,
            'is_emergency': obj.is_emergency,
            'created_on': obj.created_on,
            'created_by': obj.created_by
        }

    # def create(self, validated_data):
    #     barrier = Barrier.objects.create(**validated_data)
    #     return barrier


class BarrierReportStageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierReportStage
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_on',
            'created_by',
        )
