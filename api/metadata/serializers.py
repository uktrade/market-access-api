from rest_framework import serializers

from .fields import CategoryGroupField
from .models import BarrierPriority, BarrierTag, Category, Organisation


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
            "show_at_reporting",
            "order",
        )


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ("id", "name", "organisation_type")
