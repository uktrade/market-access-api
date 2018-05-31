from rest_framework import serializers

from api.barriers.models import Barrier
from api.barriers.company import Company


class BarrierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = '__all__'
        depth = 1


class BarrierDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = [
            'id',
            'barrier_name',
            'barrier_summary',
            'problem_status',
            'is_emergency',
            'company_id',
            'company_name',
            'export_country',
            'created_by',
            'created_on',
        ]
