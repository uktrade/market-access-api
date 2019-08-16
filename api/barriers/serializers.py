from datetime import datetime
from django.conf import settings

from django.core.cache import cache
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.utils import model_meta

from api.barriers.models import BarrierInstance
from api.core.validate_utils import DataCombiner
from api.metadata.constants import (
    ADV_BOOLEAN,
    ASSESMENT_IMPACT,
    BARRIER_SOURCE,
    BARRIER_STATUS,
    BARRIER_PENDING,
    STAGE_STATUS,
    PROBLEM_STATUS_TYPES
)
from api.core.validate_utils import DataCombiner
from api.metadata.utils import (
    get_admin_areas,
    get_barrier_types,
    get_countries,
    get_sectors,
)
from api.collaboration.models import TeamMember

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
            "resolved_date",
            "resolved_status",
            "status",
            "status_summary",
            "status_date",
            "export_country",
            "country_admin_areas",
            "sectors_affected",
            "all_sectors",
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
            "created_on",
            "modified_by",
            "modified_on",
        )

    def get_created_by(self, obj):
        if obj.created_by is None:
            return None

        return {"id": obj.created_by.id, "name": obj.created_user}

    # def validate(self, data):
    #     """
    #     Performs cross-field validation
    #     """
    #     combiner = DataCombiner(self.instance, data)

    #     sectors_affected = combiner.get_value('sectors_affected')
    #     all_sectors = combiner.get_value('all_sectors')
    #     sectors = combiner.get_value('sectors')

    #     if sectors_affected and all_sectors is None and sectors is None:
    #         raise serializers.ValidationError('missing data')

    #     if sectors_affected and all_sectors and sectors:
    #         raise serializers.ValidationError('conflicting input')

    #     return data


class BarrierCsvExportSerializer(serializers.Serializer):
    """ Serializer for CSV export """
    
    id = serializers.UUIDField()
    code = serializers.CharField()
    scope = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    barrier_title = serializers.CharField()
    sectors = serializers.SerializerMethodField()
    overseas_region = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    admin_areas = serializers.SerializerMethodField()
    barrier_types = serializers.SerializerMethodField()
    product = serializers.CharField()
    source = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    team_count = serializers.IntegerField()
    resolved_date = serializers.SerializerMethodField()
    reported_on = serializers.DateTimeField(format="%Y-%m-%d")
    modified_on = serializers.DateTimeField(format="%Y-%m-%d")
    assessment_impact = serializers.SerializerMethodField()
    value_to_economy = serializers.SerializerMethodField()
    import_market_size = serializers.SerializerMethodField()
    commercial_value = serializers.SerializerMethodField()
    export_value = serializers.SerializerMethodField()


    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "barrier_title",
            "status",
            "priority",
            "overseas_region",
            "country",
            "admin_areas",
            "sectors",
            "product",
            "scope",
            "barrier_types",
            "source",
            "team_count",
            "reported_on",
            "resolved_date",
            "modified_on",
	        "assessment_impact",
	        "value_to_economy",
	        "import_market_size",
	        "commercial_value",
	        "export_value",
        )

    def get_scope(self, obj):
        """  Custom Serializer Method Field for exposing current problem scope display value """
        print(obj.__dict__)
        problem_status_dict = dict(PROBLEM_STATUS_TYPES)
        return problem_status_dict.get(obj.problem_status, "Unknown")

    def get_assessment_impact(self, obj):
        if hasattr(obj, "assessment"):
            impact_dict = dict(ASSESMENT_IMPACT)
            return impact_dict.get(obj.assessment.impact, None)
        return None
    
    def get_value_to_economy(self, obj):
        if hasattr(obj, "assessment"):
            return obj.assessment.value_to_economy
        return None

    def get_import_market_size(self, obj):
        if hasattr(obj, "assessment"):
            return obj.assessment.import_market_size
        return None

    def get_commercial_value(self, obj):
        if hasattr(obj, "assessment"):
            return obj.assessment.commercial_value
        return None

    def get_export_value(self, obj):
        if hasattr(obj, "assessment"):
            return obj.assessment.export_value
        return None

    def get_status(self, obj):
        """  Custom Serializer Method Field for exposing current status display value """
        status_dict = dict(BARRIER_STATUS)
        sub_status_dict = dict(BARRIER_PENDING)
        status = status_dict.get(obj.status, "Unknown")
        if status == "Open: Pending action":
            status = f"{status} ({sub_status_dict.get(obj.sub_status, 'Unknown')})"
        return status

    def get_sectors(self, obj):
        if obj.sectors_affected:
            if obj.all_sectors:
                return "All"
            else:
                dh_sectors = cache.get_or_set("dh_sectors", get_sectors, 72000)
                sectors = []
                if obj.sectors:
                    for sector in obj.sectors:
                        sectors.extend([s["name"] for s in dh_sectors if s["id"] == str(sector)])
                return sectors
        else:
            return "N/A"
    
    def get_country(self, obj):
        dh_countries = cache.get_or_set("dh_countries", get_countries, 72000)
        country = [c["name"] for c in dh_countries if c["id"] == str(obj.export_country)]
        return country

    def get_overseas_region(self, obj):
        dh_countries = cache.get_or_set("dh_countries", get_countries, 72000)
        country = [c for c in dh_countries if c["id"] == str(obj.export_country)]
        if len(country) > 0:
            overseas_region = country[0].get("overseas_region", None)
            if overseas_region is not None:
                return overseas_region["name"]
        return None
    
    def get_admin_areas(self, obj):
        dh_areas = cache.get_or_set("dh_admin_areas", get_admin_areas, 72000)
        areas = []
        if obj.country_admin_areas:
            for area in obj.country_admin_areas:
                areas.extend([a["name"] for a in dh_areas if a["id"] == str(area)])
        return areas

    def get_barrier_types(self, obj):
        dh_btypes = get_barrier_types()
        btypes = []
        if obj.barrier_types:
            for btype in obj.barrier_types.all():
                btypes.append(btype.title)
        return btypes

    def get_eu_exit_related(self, obj):
        """  Custom Serializer Method Field for exposing current eu_exit_related display value """
        eu_dict = dict(ADV_BOOLEAN)
        return eu_dict.get(obj.eu_exit_related, "Unknown")

    def get_source(self, obj):
        """  Custom Serializer Method Field for exposing source display value """
        source_dict = dict(BARRIER_SOURCE)
        return source_dict.get(obj.source, "Unknown")

    def get_priority(self, obj):
        """  Custom Serializer Method Field for exposing barrier priority """
        if obj.priority:
            return obj.priority.name
        else:
            return "Unknown"

    def get_resolved_date(self, obj):
        """
        Customer field to return resolved_date if the barrier was resolved by the time it was reported
        otherwise return status_date, if current status is resolved
        """
        if obj.resolved_date:
            return obj.resolved_date
        else:
            if obj.status == 4:
                return obj.status_date

        return None


class BarrierListSerializer(serializers.ModelSerializer):
    """ Serializer for listing Barriers """

    priority = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "reported_on",
            "problem_status",
            "is_resolved",
            "resolved_date",
            "barrier_title",
            "sectors_affected",
            "all_sectors",
            "sectors",
            "export_country",
            "country_admin_areas",
            "eu_exit_related",
            "status",
            "priority",
            "barrier_types",
            "created_on",
            "modified_on",
        )

    def get_status(self, obj):
        return {
            "id": obj.status,
            "sub_status": obj.sub_status,
            "sub_status_text": obj.sub_status_other,
            "date": obj.status_date.strftime('%Y-%m-%d'),
            "summary": obj.status_summary,
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
    status = serializers.SerializerMethodField()
    has_assessment = serializers.SerializerMethodField()

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
            "all_sectors",
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
            "has_assessment",
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

    def get_status(self, obj):
        return {
            "id": obj.status,
            "sub_status": obj.sub_status,
            "sub_status_text": obj.sub_status_other,
            "date": obj.status_date.strftime('%Y-%m-%d'),
            "summary": obj.status_summary,
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

    def get_has_assessment(self, obj):
        return hasattr(obj, 'assessment')

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
        # status_summary = data.get('status_summary', None)
        # status_date = data.get('status_date', None)
        # if status_date is not None and status_summary is None:
        #     raise serializers.ValidationError('missing data')


        # if status_summary is not None:
        #     barrier = BarrierInstance.objects.get(id=self.instance.id)
        #     if barrier.status == 4:
        #         if status_date is None:
        #             raise serializers.ValidationError('missing data')
        #     else:
        #         # ignore status_date if provided
        #         data["status_date"] = getattr(self.instance, "status_date")
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
            "sub_status",
            "sub_status_other",
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
