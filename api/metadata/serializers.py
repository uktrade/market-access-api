from rest_framework import serializers

from api.metadata.fields import CategoryGroupField
from api.metadata.models import (
    BarrierPriority,
    BarrierTag,
    Category,
    ExportType,
    Organisation,
    PolicyTeam,
)


class PolicyTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyTeam
        fields = ("id", "title", "description")


class CategorySerializer(serializers.ModelSerializer):
    group = CategoryGroupField(source="category", required=False)

    class Meta:
        model = Category
        fields = (
            "id",
            "title",
            "description",
            "group",
        )


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
