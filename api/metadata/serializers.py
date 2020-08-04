from rest_framework import serializers

from api.metadata.models import BarrierPriority, BarrierTag, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "title",
            "description",
            "category",
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
