from rest_framework import serializers

from api.barriers.models import Barrier, BarrierReportStage
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

    def to_representation(self, obj):
        return {
            'id': obj.id,
            'company_name': obj.company_name
        }

    def create(self, validated_data):
        # barrier = Barrier(
        #     problem_status=validated_data["problem_status"],
        #     is_emergency=validated_data["is_emergency"],
        #     company_id=validated_data["company_id"],
        #     company_name=validated_data["company_name"],
        #     contact_id=validated_data["contact_id"],
        #     product=validated_data["product"],
        #     export_country=validated_data["export_country"],
        #     problem_description=validated_data["problem_description"],
        #     problem_impact=validated_data["problem_impact"],
        #     estimated_loss_range=validated_data["estimated_loss_range"],
        #     other_companies_affected=validated_data["other_companies_affected"],
        #     govt_response_requester=validated_data["govt_response_requester"],
        #     is_confidential=validated_data["is_confidential"],
        #     sensitivity_summary=validated_data["sensitivity_summary"],
        #     can_publish=validated_data["can_publish"],
        #     barrier_name=validated_data["barrier_name"],
        #     commodity_codes=validated_data["commodity_codes"],
        #     barrier_summary=validated_data["barrier_summary"],
        # )
        # # user.set_password(validated_data['password'])
        # barrier.save()
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


class BarrierReportStageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierReportStage
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_on',
            'created_by',
        )
