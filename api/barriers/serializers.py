from django.conf import settings

from django.shortcuts import get_object_or_404

from rest_framework import serializers

from api.barriers.models import BarrierInstance
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
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "problem_status",
            "is_resolved",
            "status",
            "status_summary",
            "status_date",
            "resolved_date",
            "export_country",
            "sectors_affected",
            "sectors",
            "product",
            "source",
            "other_source",
            "barrier_title",
            "problem_description",
            "next_steps_summary",
            "eu_exit_related",
            "progress",
            "created_by",
            "created_on",
            "modified_by",
            "modified_on"
        )
        read_only_fields = (
            "id",
            "code",
            "status",
            "status_date",
            "progress",
            "created_by",
            "created_on"
            "modified_by",
            "modified_on"
        )

    def get_created_by(self, obj):
        return obj.created_user


class BarrierListSerializer(serializers.ModelSerializer):
    """ Serializer for listing Barriers """

    current_status = serializers.SerializerMethodField()
    reported_by = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "reported_on",
            "reported_by",
            "problem_status",
            "is_resolved",
            "resolved_date",
            "barrier_title",
            "sectors_affected",
            "sectors",
            "export_country",
            "current_status",
            "priority",
            "barrier_type",
            "barrier_type_category",
            "created_on",
        )

    def get_reported_by(self, obj):
        return obj.created_user

    def get_current_status(self, obj):
        """  Custom Serializer Method Field for exposing current barrier status as json """
        return {
            "status": obj.status,
            "status_date": obj.status_date,
            "status_summary": obj.status_summary,
        }

    def get_priority(self, obj):
        """  Custom Serializer Method Field for exposing barrier priority """
        if obj.priority:
            return {
                "code": obj.priority.code,
                "name": obj.priority.name,
                "order": obj.priority.order,
            }
        else:
            return {
                "code": "UNKNOWN",
                "name": "Unknown",
                "order": 0,
            }


class BarrierInstanceSerializer(serializers.ModelSerializer):
    """ Serializer for Barrier Instance """

    current_status = serializers.SerializerMethodField()
    reported_by = serializers.SerializerMethodField()
    barrier_type = serializers.SerializerMethodField()
    modified_by = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "problem_status",
            "is_resolved",
            "resolved_date",
            "export_country",
            "sectors_affected",
            "sectors",
            "companies",
            "product",
            "source",
            "other_source",
            "barrier_title",
            "problem_description",
            "barrier_type",
            "barrier_type_category",
            "reported_on",
            "reported_by",
            "current_status",
            "priority",
            "priority_summary",
            "eu_exit_related",
            "created_on",
            "modified_by",
            "modified_on",
        )
        read_only_fields = (
            "id",
            "code",
            "reported_on",
            "reported_by",
            "priority_date",
            "created_on",
            "modified_on",
            "modifieds_by",
        )
        depth = 1

    def reported_on(self, obj):
        return obj.created_on

    def get_reported_by(self, obj):
        return obj.created_user

    def get_modified_by(self, obj):
        return obj.modified_user

    def get_barrier_type(self, obj):
        if obj.barrier_type is None:
            return None
        else:
            return {
                "id": obj.barrier_type.id,
                "title": obj.barrier_type.title,
                "description": obj.barrier_type.description,
                "category": obj.barrier_type_category,
            }

    def get_current_status(self, obj):
        return {
            "status": obj.status,
            "status_date": obj.status_date,
            "status_summary": obj.status_summary,
        }

    def get_priority(self, obj):
        """  Custom Serializer Method Field for exposing barrier priority """
        if obj.priority:
            return {
                "code": obj.priority.code,
                "name": obj.priority.name,
                "order": obj.priority.order,
            }
        else:
            return {
                "code": "UNKNOWN",
                "name": "Unknown",
                "order": 0,
            }


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
            "created_by",
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
            "created_by",
        )
        read_only_fields = (
            "id",
            "status",
            "status_date",
            "is_active",
            "created_on",
            "created_by",
        )
