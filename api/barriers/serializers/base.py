from rest_framework import serializers

from api.assessment.serializers import (
    AssessmentSerializer,
    ResolvabilityAssessmentSerializer,
    StrategicAssessmentSerializer,
)
from api.barriers.fields import (
    ArchivedField,
    ArchivedReasonField,
    BarrierPriorityField,
    CategoriesField,
    CommoditiesField,
    PublicEligibilityField,
    SectorsField,
    SourceField,
    StatusField,
    SubStatusField,
    TagsField,
    TermField,
    TradeDirectionField,
    UserField,
    WTOProfileField,
)
from api.barriers.models import Barrier, BarrierUserHit
from api.core.serializers.mixins import CustomUpdateMixin
from api.metadata.fields import AdminAreasField, CountryField, TradingBlocField
from .mixins import LocationFieldMixin
from .public_barriers import NestedPublicBarrierSerializer


class BarrierSerializerBase(LocationFieldMixin, CustomUpdateMixin, serializers.ModelSerializer):
    admin_areas = AdminAreasField(required=False)
    archived = ArchivedField(required=False)
    archived_by = UserField(required=False)
    archived_reason = ArchivedReasonField(required=False)
    assessment = AssessmentSerializer(required=False)
    resolvability_assessments = ResolvabilityAssessmentSerializer(required=False, many=True)
    strategic_assessments = StrategicAssessmentSerializer(required=False, many=True)
    categories = CategoriesField(required=False)
    commodities = CommoditiesField(source="barrier_commodities", required=False)
    country = CountryField(required=False, allow_null=True)
    created_by = UserField(required=False)
    has_assessment = serializers.SerializerMethodField()
    last_seen_on = serializers.SerializerMethodField()
    modified_by = UserField(required=False)
    priority = BarrierPriorityField(required=False)
    sectors = SectorsField(required=False)
    source = SourceField(required=False)
    status = StatusField(required=False)
    sub_status = SubStatusField(required=False, allow_blank=True)
    public_barrier = NestedPublicBarrierSerializer(required=False)
    public_eligibility = PublicEligibilityField(required=False)
    term = TermField(required=False, allow_null=True)
    tags = TagsField(required=False)
    title = serializers.CharField(required=False)
    trade_direction = TradeDirectionField(required=False)
    trading_bloc = TradingBlocField(required=False, allow_blank=True)
    unarchived_by = UserField(required=False)
    wto_profile = WTOProfileField(required=False)

    class Meta:
        model = Barrier
        read_only_fields = (
            "archived_by",
            "archived_on",
            "code",
            "created_by",
            "created_on",
            "id",
            "last_seen_on",
            "location",
            "modified_by",
            "modified_on",
            "priority_date",
            "resolvability_assessments",
            "strategic_assessments",
            "unarchived_by",
            "unarchived_on",
        )

    def get_has_assessment(self, obj):
        return hasattr(obj, 'assessment')

    def get_last_seen_on(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            hit, _created = BarrierUserHit.objects.get_or_create(user=request.user, barrier=obj)
            last_seen = hit.last_seen
            hit.save()
            return last_seen

    def validate_public_eligibility(self, attrs):
        """ Check for permissions here """
        # TODO: check user permissions - this field should only be updated
        #       by the publishing team
        return attrs

    def validate_public_eligibility_summary(self, attrs):
        """ Check for permissions here """
        # TODO: check user permissions - this field should only be updated
        #       by the publishing team
        return attrs
