from rest_framework import serializers

from api.assessment.serializers import AssessmentSerializer
from api.barriers.fields import (
    AdminAreasField,
    BarrierPriorityField,
    CategoriesField,
    CountryField,
    ScopeField,
    SectorsField,
    SourceField,
    StatusField,
    TagsField,
    UsernameField,
)
from api.barriers.models import BarrierInstance, BarrierUserHit, BarrierCommodity
from api.collaboration.models import TeamMember
from api.commodities.models import Commodity
from api.commodities.serializers import BarrierCommoditySerializer
from api.interactions.models import Document
from api.wto.models import WTOProfile
from api.wto.serializers import WTOProfileSerializer
from api.barriers.fields import PublicEligibilityField
from .public_barriers import NestedPublicBarrierSerializer


class BarrierSerializerBase(serializers.ModelSerializer):
    admin_areas = AdminAreasField(source="country_admin_areas", required=False)
    archived_by = UsernameField(required=False)
    assessment = AssessmentSerializer(required=False)
    categories = CategoriesField(required=False)
    commodities = BarrierCommoditySerializer(source="barrier_commodities", many=True, required=False)
    country = CountryField(source="export_country", required=False)
    created_by = UsernameField(required=False)
    has_assessment = serializers.SerializerMethodField()
    last_seen_on = serializers.SerializerMethodField()
    modified_by = UsernameField(required=False)
    priority = BarrierPriorityField(required=False)
    sectors = SectorsField(required=False)
    source = SourceField(required=False)
    status = StatusField(required=False)
    public_barrier = NestedPublicBarrierSerializer()
    public_eligibility = PublicEligibilityField(required=False)
    scope = ScopeField(source="problem_status")
    tags = TagsField(required=False)
    title = serializers.CharField(source="barrier_title", required=False)
    wto_profile = WTOProfileSerializer()

    class Meta:
        model = BarrierInstance
        read_only_fields = (
            "archived_by",
            "archived_on",
            "code",
            "created_by",
            "created_on",
            "id",
            "last_seen_on",
            "modified_by",
            "modified_on",
            "priority_date",
            "unarchived_by",
            "unarchived_on",
        )

    def get_has_assessment(self, obj):
        return hasattr(obj, 'assessment')

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

    def validate_trade_direction(self, attrs):
        if not attrs:
            raise serializers.ValidationError('Field is not nullable.')
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
        return super().save(*args, **kwargs)


class BarrierDetailSerializer(BarrierSerializerBase):
    class Meta(BarrierSerializerBase.Meta):
        fields = (
            "admin_areas",
            "assessment",
            "all_sectors",
            "archived",
            "archived_by",
            "archived_explanation",
            "archived_on",
            "archived_reason",
            "barrier_title",
            "categories",
            "code",
            "commodities",
            "companies",
            "country",
            "created_by",
            "created_on",
            "end_date",
            "has_assessment",
            "id",
            "is_summary_sensitive",
            "last_seen_on",
            "modified_by",
            "modified_on",
            "other_source",
            "priority",
            "priority_summary",
            "problem_status",
            "product",
            "public_barrier",
            "public_eligibility",
            "public_eligibility_summary",
            "scope",
            "sectors",
            "sectors_affected",
            "source",
            "status",
            "status_date",
            "status_summary",
            "sub_status",
            "sub_status_other",
            "summary",
            "tags",
            "title",
            "trade_direction",
            "unarchived_by",
            "unarchived_on",
            "unarchived_reason",
            "wto_profile",
        )


class BarrierListSerializer(BarrierSerializerBase):
    class Meta(BarrierSerializerBase.Meta):
        fields = (
            "admin_areas",
            "all_sectors",
            "archived",
            "archived_on",
            "categories",
            "code",
            "country",
            "created_on",
            "id",
            "modified_on",
            "priority",
            "problem_status",
            "reported_on",
            "sectors",
            "sectors_affected",
            "status",
            "status_date",
            "status_summary",
            "tags",
            "title",
            "trade_direction",
        )


class DataWorkspaceSerializer(BarrierSerializerBase):
    team_count = serializers.SerializerMethodField()

    class Meta(BarrierSerializerBase.Meta):
        fields = (
            "admin_areas",
            "assessment",
            "categories",
            "code",
            "companies",
            "country",
            "id",
            "modified_on",
            "priority",
            "product",
            "scope",
            "sectors",
            "source",
            "status",
            "status_date",
            "team_count",
            "title",
        )

    def get_team_count(self, obj):
        return TeamMember.objects.filter(barrier=obj).count()


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
