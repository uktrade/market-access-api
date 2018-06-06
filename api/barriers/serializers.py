from rest_framework import serializers

from api.barriers.models import Barrier
from api.barriers.company import Company


class BarrierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = [
            'id',
            'created_on',
            'created_by',
            'company_name',
        ]
        read_only_fields = (
            'id',
            'created_on',
            'created_by',
        )

        depth = 1


class BarrierDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barrier
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_on',
            'created_by',
        )
