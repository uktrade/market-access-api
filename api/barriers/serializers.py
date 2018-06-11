from rest_framework import serializers

from api.barriers.models import Barrier, BarrierReportStage, ReportStage
from api.barriers.company import Company


class BarrierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_on',
            'created_by',
        )
        depth = 1

    def to_representation(self, obj):
        return {
            'id': obj.id,
            'company_id': obj.company_id,
            'company_name': obj.company_name,
            'status': obj.status
        }

    def create(self, validated_data):
        barrier = Barrier.objects.create(**validated_data)
        return barrier


class BarrierDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_on',
            'created_by',
        )
        depth = 2

    def update(self, validated_data):
        print(validated_data)


class BarrierReportStageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierReportStage
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_on',
            'created_by',
        )
