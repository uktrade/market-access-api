from django.conf import settings

from rest_framework import serializers

from api.barriers.models import BarrierInstance, BarrierUserHit
from api.collaboration.models import TeamMember
from api.hs_codes.serializers import HSCodeSerializer
from api.interactions.models import Document
from api.metadata.constants import (
    ASSESMENT_IMPACT,
    BARRIER_SOURCE,
    BARRIER_STATUS,
    BARRIER_PENDING,
    STAGE_STATUS,
    PROBLEM_STATUS_TYPES,
    TRADE_DIRECTION_CHOICES,
)
from api.metadata.models import HSCode
from api.metadata.serializers import BarrierTagSerializer
from api.metadata.utils import (
    adjust_barrier_tags,
    get_admin_area,
    get_country,
    get_sector,
)
from api.wto.models import WTOProfile
from api.wto.serializers import WTOProfileSerializer


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
    tags = serializers.SerializerMethodField()
    # TODO: deprecate this field (use summary instead)
    problem_description = serializers.CharField(source="summary", required=False)

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "problem_status",
            "status",
            "status_summary",
            "status_date",
            "sub_status",
            "sub_status_other",
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
            "summary",
            "is_summary_sensitive",
            "next_steps_summary",
            "progress",
            "created_by",
            "created_on",
            "modified_by",
            "modified_on",
            "tags",
            "trade_direction",
        )
        read_only_fields = (
            "id",
            "code",
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

    def get_tags(self, obj):
        tags = obj.tags.all()
        serializer = BarrierTagSerializer(tags, many=True)
        return serializer.data

    def validate_tags(self, tag_ids=None):
        if tag_ids is not None and type(tag_ids) is not list:
            raise serializers.ValidationError('Expected a list of tag IDs.')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Tags
        tag_ids = self.context["request"].data.get("tags")
        self.validate_tags(tag_ids)

        return attrs

    def save(self, *args, **kwargs):
        barrier = super().save(*args, **kwargs)
        # Tags
        tag_ids = self.initial_data.get("tags")
        adjust_barrier_tags(barrier, tag_ids)


class BarrierCsvExportSerializer(serializers.Serializer):
    """ Serializer for CSV export """

    id = serializers.UUIDField()
    code = serializers.CharField()
    scope = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_date = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    barrier_title = serializers.CharField()
    sectors = serializers.SerializerMethodField()
    overseas_region = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    admin_areas = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    product = serializers.CharField()
    source = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    team_count = serializers.IntegerField()
    reported_on = serializers.DateTimeField(format="%Y-%m-%d")
    modified_on = serializers.DateTimeField(format="%Y-%m-%d")
    assessment_impact = serializers.SerializerMethodField()
    value_to_economy = serializers.SerializerMethodField()
    import_market_size = serializers.SerializerMethodField()
    commercial_value = serializers.SerializerMethodField()
    export_value = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    trade_direction = serializers.SerializerMethodField()
    end_date = serializers.DateField(format="%Y-%m-%d")
    link = serializers.SerializerMethodField()
    economic_assessment_explanation = serializers.SerializerMethodField()
    wto_has_been_notified = serializers.SerializerMethodField()
    wto_should_be_notified = serializers.SerializerMethodField()
    wto_committee_notified = serializers.CharField(
        source="wto_profile.committee_notified.name",
        default="",
    )
    wto_committee_notification_link = serializers.CharField(
        source="wto_profile.committee_notification_link",
        default="",
    )
    wto_member_states = serializers.SerializerMethodField()
    wto_committee_raised_in = serializers.CharField(
        source="wto_profile.committee_raised_in.name",
        default="",
    )
    wto_raised_date = serializers.DateField(
        source="wto_profile.raised_date",
        default="",
        format="%Y-%m-%d",
    )
    wto_case_number = serializers.CharField(
        source="wto_profile.case_number",
        default="",
    )

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "barrier_title",
            "status",
            "status_date",
            "priority",
            "overseas_region",
            "country",
            "admin_areas",
            "sectors",
            "product",
            "scope",
            "source",
            "team_count",
            "priority",
            "team_count",
            "reported_on",
            "modified_on",
            "assessment_impact",
            "value_to_economy",
            "import_market_size",
            "commercial_value",
            "export_value",
            "end_date",
            "link",
            "economic_assessment_explanation",
        )

    def get_scope(self, obj):
        """  Custom Serializer Method Field for exposing current problem scope display value """
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

    def get_status_date(self, obj):
        if obj.status_date:
            return obj.status_date.strftime("%Y-%m-%d")
        else:
            return None

    def get_summary(self, obj):
        if obj.is_summary_sensitive:
            return "OFFICIAL-SENSITIVE (see it on DMAS)"
        else:
            return obj.summary or None

    def get_sectors(self, obj):
        if obj.sectors_affected:
            if obj.all_sectors:
                return "All"
            else:
                sector_names = []
                for sector_id in obj.sectors:
                    sector = get_sector(str(sector_id))
                    if sector and sector.get("name"):
                        sector_names.append(sector.get("name"))
                return sector_names
        else:
            return "N/A"

    def get_country(self, obj):
        country = get_country(str(obj.export_country))
        if country:
            return country.get("name")

    def get_overseas_region(self, obj):
        country = get_country(str(obj.export_country))
        if country:
            overseas_region = country.get("overseas_region")
            if overseas_region:
                return overseas_region.get("name")

    def get_admin_areas(self, obj):
        admin_area_names = []
        for admin_area in obj.country_admin_areas or []:
            admin_area = get_admin_area(str(admin_area))
            if admin_area and admin_area.get("name"):
                admin_area_names.append(admin_area.get("name"))
        return admin_area_names

    def get_categories(self, obj):
        return [category.title for category in obj.categories.all()]

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

    def get_team_count(self, obj):
        if hasattr(obj, "team_count"):
            return obj.team_count
        return TeamMember.objects.filter(barrier=obj).count()

    def get_tags(self, obj):
        return [tag.title for tag in obj.tags.all()]

    def get_trade_direction(self, obj):
        if obj.trade_direction:
            trade_directions = dict((str(x), y) for x, y in TRADE_DIRECTION_CHOICES)
            return trade_directions.get(str(obj.trade_direction))
        else:
            return None

    def get_link(self, obj):
        return f"{settings.DMAS_BASE_URL}/barriers/{obj.code}"

    def get_economic_assessment_explanation(self, obj):
        if obj.has_assessment:
            return obj.assessment.explanation
        else:
            return None

    def get_wto_has_been_notified(self, obj):
        if obj.wto_profile:
            if obj.wto_profile.wto_has_been_notified is True:
                return "Yes"
            elif obj.wto_profile.wto_has_been_notified is False:
                return "No"

    def get_wto_should_be_notified(self, obj):
        if obj.wto_profile:
            if obj.wto_profile.wto_should_be_notified is True:
                return "Yes"
            elif obj.wto_profile.wto_should_be_notified is False:
                return "No"

    def get_wto_member_states(self, obj):
        if obj.wto_profile:
            return [
                get_country(str(country_id)).get("name")
                for country_id in obj.wto_profile.member_states
            ]


class BarrierListSerializer(serializers.ModelSerializer):
    """ Serializer for listing Barriers """

    priority = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    tags = BarrierTagSerializer(many=True)

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "reported_on",
            "problem_status",
            "barrier_title",
            "sectors_affected",
            "all_sectors",
            "sectors",
            "export_country",
            "country_admin_areas",
            "status",
            "status_date",
            "status_summary",
            "priority",
            "categories",
            "tags",
            "trade_direction",
            "created_on",
            "modified_on",
            "archived",
            "archived_on",
        )

    def get_categories(self, obj):
        return [category.id for category in obj.categories.all()]

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

    archived_by = serializers.SerializerMethodField()
    reported_by = serializers.SerializerMethodField()
    modified_by = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    barrier_types = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    has_assessment = serializers.SerializerMethodField()
    last_seen_on = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    # TODO: deprecate this field (use summary instead)
    problem_description = serializers.CharField(source="summary", required=False)
    wto_profile = WTOProfileSerializer()
    hs_codes = HSCodeSerializer(many=True, required=False)

    class Meta:
        model = BarrierInstance
        fields = (
            "id",
            "code",
            "problem_status",
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
            "summary",
            "is_summary_sensitive",
            "barrier_types",
            "categories",
            "reported_on",
            "reported_by",
            "status",
            "status_summary",
            "status_date",
            "priority",
            "priority_summary",
            "has_assessment",
            "created_on",
            "modified_by",
            "modified_on",
            "archived",
            "archived_on",
            "archived_by",
            "archived_reason",
            "archived_explanation",
            "unarchived_reason",
            "unarchived_on",
            "unarchived_by",
            "last_seen_on",
            "tags",
            "trade_direction",
            "end_date",
            "wto_profile",
            "hs_codes",
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
            "archived_on",
            "archived_by",
            "unarchived_on",
            "unarchived_by",
            "last_seen_on",
        )
        depth = 1

    def reported_on(self, obj):
        return obj.created_on

    def get_archived_by(self, obj):
        return obj.archived_user

    def get_unarchived_by(self, obj):
        return obj.unarchived_user

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
        return self.get_categories(obj)

    def get_categories(self, obj):
        return [category.id for category in obj.categories.all()]

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

    def get_last_seen_on(self, obj):
        user = None
        hit = None
        last_seen = None

        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
            hit, _created = BarrierUserHit.objects.get_or_create(user=user, barrier=obj)
            last_seen = hit.last_seen

        if user:
            hit.save()

        return last_seen

    def get_tags(self, obj):
        tags = obj.tags.all()
        serializer = BarrierTagSerializer(tags, many=True)
        return serializer.data

    def validate_tags(self, tag_ids=None):
        if tag_ids is not None and type(tag_ids) is not list:
            raise serializers.ValidationError('Expected a list of tag IDs.')

    def validate_trade_direction(self, attrs):
        if not attrs:
            raise serializers.ValidationError('Field is not nullable.')
        return attrs

    def validate(self, attrs):
        attrs = super().validate(attrs)

        # Tags
        tag_ids = self.context["request"].data.get("tags")
        self.validate_tags(tag_ids)

        return attrs

    def update(self, instance, validated_data):
        if "wto_profile" in validated_data:
            self.update_wto_profile(instance, validated_data)

        if "hs_codes" in validated_data:
            self.update_hs_codes(instance, validated_data)

        if instance.archived is False and validated_data.get("archived") is True:
            instance.archive(
                user=self.user,
                reason=validated_data.get("archived_reason"),
                explanation=validated_data.get("archived_explanation"),
            )
        elif instance.archived is True and validated_data.get("archived") is False:
            instance.unarchive(
                user=self.user,
                reason=validated_data.get("unarchived_reason"),
            )
        return super().update(instance, validated_data)

    def update_hs_codes(self, instance, validated_data):
        hs_codes = validated_data.pop('hs_codes')
        codes = [hs_code.get("code") for hs_code in hs_codes]
        hs_codes = HSCode.objects.filter(code__in=codes)
        instance.hs_codes.set(hs_codes)

    def update_wto_profile(self, instance, validated_data):
        wto_profile = validated_data.pop('wto_profile')
        if wto_profile:
            document_fields = ("committee_notification_document", "meeting_minutes")
            for field_name in document_fields:
                if field_name in self.initial_data["wto_profile"]:
                    document_id = self.initial_data["wto_profile"].get(field_name)
                    if document_id:
                        try:
                            Document.objects.get(pk=document_id)
                        except Document.DoesNotExist:
                            continue
                    wto_profile[f"{field_name}_id"] = document_id

            WTOProfile.objects.update_or_create(barrier=instance, defaults=wto_profile)

    def save(self, *args, **kwargs):
        self.user = kwargs.get("modified_by")
        barrier = super().save(*args, **kwargs)
        # Tags
        tag_ids = self.initial_data.get("tags")
        adjust_barrier_tags(barrier, tag_ids)


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
