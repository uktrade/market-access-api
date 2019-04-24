from datetime import datetime
from django.conf import settings

from django.shortcuts import get_object_or_404

from rest_framework import serializers

from api.barriers.models import BarrierInstance
from api.core.validate_utils import DataCombiner
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
            "country_admin_areas",
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
            "modified_on",
        )
        read_only_fields = (
            "id",
            "code",
            "status",
            "status_date",
            "progress",
            "created_by",
            "created_on" "modified_by",
            "modified_on",
        )

    def get_created_by(self, obj):
        return obj.created_user


class BarrierListSerializer(serializers.ModelSerializer):
    """ Serializer for listing Barriers """

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
            "country_admin_areas",
            "eu_exit_related",
            "status",
            "status_date",
            "status_summary",
            "priority",
            "barrier_types",
            "created_on",
            "modified_on",
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
            return {"code": "UNKNOWN", "name": "Unknown", "order": 0}


class BarrierInstanceSerializer(serializers.ModelSerializer):
    """ Serializer for Barrier Instance """

    reported_by = serializers.SerializerMethodField()
    modified_by = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    barrier_types = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "problem_status",
            "is_resolved",
            "resolved_date",
            "export_country",
            "country_admin_areas",
            "sectors_affected",
            "sectors",
            "companies",
            "product",
            "source",
            "other_source",
            "barrier_title",
            "problem_description",
            "barrier_types",
            "reported_on",
            "reported_by",
            "status",
            "status_summary",
            "status_date",
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
            "status",
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

    def get_current_status(self, obj):
        return {
            "status": obj.status,
            "status_date": obj.status_date,
            "status_summary": obj.status_summary,
        }

    def get_barrier_types(self, obj):
        return [barrier_type.id for barrier_type in obj.barrier_types.all()]

    def get_priority(self, obj):
        """  Custom Serializer Method Field for exposing barrier priority """
        if obj.priority:
            return {
                "code": obj.priority.code,
                "name": obj.priority.name,
                "order": obj.priority.order,
            }
        else:
            return {"code": "UNKNOWN", "name": "Unknown", "order": 0}

    def _get_value(self, source1, source2, field_name):
        if field_name in source1:
            return source1[field_name]
        if field_name in source2:
            return source2[field_name]
        return None

    def validate(self, data):
        """
        Performs cross-field validation
        status validations:
        if status_summary is provided, status_date is mandatory 
            when current status is Resolved
        if status_date is provided, status_summary is also expected
        """
        status_summary = data.get('status_summary', None)
        status_date = data.get('status_date', None)
        if status_date is not None and status_summary is None:
            raise serializers.ValidationError('missing data')
        
        if status_summary is not None:
            barrier = BarrierInstance.objects.get(id=self.instance.id)
            if barrier.status == 4:
                if status_date is None:
                    raise serializers.ValidationError('missing data')
            else:
                # ignore status_date if provided
                data["status_date"] = getattr(self.instance, "status_date")
        return data


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
