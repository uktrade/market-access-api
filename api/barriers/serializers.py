
from rest_framework import serializers

from api.barriers.models import (
    BarrierContributor,
    BarrierInstance,
    BarrierInteraction,
    BarrierStatus
)
from api.metadata.constants import STAGE_STATUS

# pylint: disable=R0201

class BarrierReportStageListingField(serializers.RelatedField):
    def to_representation(self, value):
        stage_status_dict = dict(STAGE_STATUS)
        return {
            "stage_code": value.stage.code,
            "stage_desc": value.stage.description,
            "status_id": value.status,
            "status_desc": stage_status_dict[value.status],
        }


class BarrierReportSerializer(serializers.ModelSerializer):
    progress = BarrierReportStageListingField(many=True, read_only=True)
    reported_by = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "problem_status",
            "is_resolved",
            "resolved_date",
            "export_country",
            "sectors_affected",
            "sectors",
            "product",
            "source",
            "other_source",
            "barrier_title",
            "problem_description",
            "barrier_type",
            "progress",
            "reported_by",
            "created_on"
        )
        read_only_fields = ("id", "progress", "created_on")

    def get_reported_by(self, obj):
        return obj.created_by.email if obj.created_by else ""


class BarrierListSerializer(serializers.ModelSerializer):
    """ Serializer for listing Barriers """
    current_status = serializers.SerializerMethodField()
    contributor_count = serializers.SerializerMethodField()
    reported_by = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "reported_on",
            "reported_by",
            "problem_status",
            "is_resolved",
            "barrier_title",
            "export_country",
            "contributor_count",
            "current_status",
            "created_on"
        )

    def get_reported_by(self, obj):
        return obj.created_by.email if obj.created_by else ""

    def get_current_status(self, obj):
        """  Custom Serializer Method Field for exposing current barrier status as json """
        # barrier_status = BarrierStatus.objects.filter(barrier=obj).latest("created_on")
        return {
            "status": obj.status,
            "status_date": obj.status_date,
            "status_summary": obj.status_summary,
        }

    def get_contributor_count(self, obj):
        """ Custom Serializer Method Field for barrier count """
        barrier_contributors_count = BarrierContributor.objects.filter(
            barrier=obj,
            is_active=True
        ).count()
        return barrier_contributors_count


class BarrierInstanceSerializer(serializers.ModelSerializer):
    """ Serializer for Barrier Instance """
    current_status = serializers.SerializerMethodField()
    reported_by = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "problem_status",
            "is_resolved",
            "resolved_date",
            "export_country",
            "sectors_affected",
            "sectors",
            "product",
            "source",
            "other_source",
            "barrier_title",
            "problem_description",
            "barrier_type",
            "reported_on",
            "reported_by",
            "current_status",
            "created_on"
        )
        depth = 1

    def reported_on(self, obj):
        return obj.created_on

    def get_reported_by(self, obj):
        return obj.created_by.email if obj.created_by else ""

    def get_current_status(self, obj):
        return {
            "status": obj.status,
            "status_date": obj.status_date,
            "status_summary": obj.status_summary,
        }


class BarrierInteractionSerializer(serializers.ModelSerializer):
    """ Serialzer for Barrier Ineractions """
    class Meta:
        model = BarrierInteraction
        fields = "__all__"
        read_only_fields = ("barrier", "kind", "created_on", "created_by")


class BarrierContributorSerializer(serializers.ModelSerializer):
    """ Serializer for Barrier Contributors """
    class Meta:
        model = BarrierContributor
        fields = "__all__"
        read_only_fields = ("barrier", "created_on", "created_by")


class BarrierResolveSerializer(serializers.ModelSerializer):
    """ Serializer for resolving a barrier """
    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "status",
            "status_date",
            "status_summary",
            "created_on",
            "created_by"
        )
        read_only_fields = ("id", "status", "created_on", "created_by")


class BarrierStaticStatusSerializer(serializers.ModelSerializer):
    """ generic serializer for other barrier statuses """
    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "status",
            "status_date",
            "status_summary",
            "created_on",
            "created_by"
        )
        read_only_fields = (
            "id",
            "status",
            "status_date",
            "is_active",
            "created_on",
            "created_by"
        )

