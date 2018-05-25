from rest_framework import serializers

from api.barriers.models import Barrier
from api.barriers.company import Company


class BarrierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = [
            'id',
            'title',
            'description',
            'status',
            'is_emergency',
            'company_id',
            'company_name',
            'export_country',
            'created_on',
        ]


class BarrierDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = [
            'id',
            'title',
            'description',
            'status',
            'is_emergency',
            'company_id',
            'company_name',
            'export_country',
            'created_on',
        ]
