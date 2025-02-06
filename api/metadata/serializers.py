from rest_framework import serializers

from api.metadata.models import (
    BarrierPriority,
    BarrierTag,
    ExportType,
    Organisation,
    PolicyTeam,
)


class PolicyTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyTeam
        fields = ("id", "title", "description")


class BarrierPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierPriority
        fields = (
            "code",
            "name",
            "order",
        )


class BarrierTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierTag
        fields = (
            "id",
            "title",
            "description",
            "is_top_priority_tag",
            "show_at_reporting",
            "order",
        )


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ("id", "name", "organisation_type")


class ExportTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportType
        fields = (
            "id",
            "name",
        )
