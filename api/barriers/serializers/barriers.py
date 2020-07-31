from rest_framework import serializers

from api.barriers.models import BarrierInstance, BarrierUserHit, BarrierCommodity

from api.commodities.models import Commodity
from api.commodities.serializers import BarrierCommoditySerializer

from api.interactions.models import Document

from api.metadata.serializers import BarrierTagSerializer
from api.metadata.utils import (
    adjust_barrier_tags,
)
from api.wto.models import WTOProfile
from api.wto.serializers import WTOProfileSerializer
from api.barriers.fields import PublicEligibilityField
from .public_barriers import NestedPublicBarrierSerializer

# pylint: disable=R0201


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
    public_barrier = NestedPublicBarrierSerializer()
    public_eligibility = PublicEligibilityField()
    wto_profile = WTOProfileSerializer()
    commodities = BarrierCommoditySerializer(source="barrier_commodities", many=True, required=False)

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
            "commodities",
            "public_barrier",
            "public_eligibility",
            "public_eligibility_summary",
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

    def validate_public_eligibility(self, attrs):
        """ Check for permissions here """
        if type(attrs) is not bool:
            raise serializers.ValidationError('Expected a boolean.')

        # TODO: check user permissions - this field should only be updated
        #       by the publishing team

        return attrs

    def validate_public_eligibility_summary(self, attrs):
        """ Check for permissions here """
        # TODO: check user permissions - this field should only be updated
        #       by the publishing team
        return attrs

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

        if "barrier_commodities" in validated_data:
            self.update_commodities(instance, validated_data)

        if (
            "public_eligibility" in validated_data
            and "public_eligibility_summary" not in validated_data
        ):
            validated_data["public_eligibility_summary"] = ""

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

    def update_commodities(self, instance, validated_data):
        commodities_data = validated_data.pop('barrier_commodities')

        added_commodities = []

        for commodity_data in commodities_data:
            code = commodity_data.get("code").ljust(10, "0")
            country = commodity_data.get("country")
            hs6_code = code[:6].ljust(10, "0")
            commodity = Commodity.objects.filter(code=hs6_code, is_leaf=True).latest("version")
            barrier_commodity, created = BarrierCommodity.objects.get_or_create(
                barrier=self.instance,
                commodity=commodity,
                code=code,
                country=country,
            )
            added_commodities.append(barrier_commodity.id)

        BarrierCommodity.objects.filter(barrier=instance).exclude(id__in=added_commodities).delete()

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
