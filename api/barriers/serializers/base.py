import logging

from django.forms import BooleanField
from rest_framework import serializers

from api.assessment.serializers import (
    EconomicAssessmentSerializer,
    EconomicImpactAssessmentSerializer,
    ResolvabilityAssessmentSerializer,
    StrategicAssessmentSerializer,
)
from api.barriers.fields import (
    ArchivedField,
    ArchivedReasonField,
    BarrierPriorityField,
    CommoditiesField,
    ExportTypesField,
    OrganisationsField,
    PolicyTeamsField,
    PublicEligibilityField,
    SectorField,
    SectorsField,
    SourceField,
    StatusField,
    SubStatusField,
    TagsField,
    TermField,
    TradeCategoryField,
    TradeDirectionField,
    UserField,
    WTOProfileField,
)
from api.barriers.models import Barrier, BarrierUserHit
from api.barriers.serializers.progress_updates import (
    NextStepItemSerializer,
    ProgrammeFundProgressUpdateSerializer,
    ProgressUpdateSerializer,
)
from api.core.serializers.mixins import CustomUpdateMixin
from api.metadata.fields import AdminAreasField, CountryField, TradingBlocField

from .mixins import LocationFieldMixin
from .public_barriers import NestedPublicBarrierSerializer

logger = logging.getLogger(__name__)


class BarrierSerializerBase(
    LocationFieldMixin,
    CustomUpdateMixin,
    serializers.ModelSerializer,
):
    admin_areas = AdminAreasField(required=False)
    caused_by_admin_areas = BooleanField(required=False)
    archived = ArchivedField(required=False)
    archived_by = UserField(required=False)
    archived_reason = ArchivedReasonField(required=False)
    economic_assessments = EconomicAssessmentSerializer(required=False, many=True)
    valuation_assessments = EconomicImpactAssessmentSerializer(
        required=False, many=True
    )
    resolvability_assessments = ResolvabilityAssessmentSerializer(
        required=False, many=True
    )
    strategic_assessments = StrategicAssessmentSerializer(required=False, many=True)
    policy_teams = PolicyTeamsField(required=False)
    commodities = CommoditiesField(source="barrier_commodities", required=False)
    country = CountryField(required=False, allow_null=True)
    created_by = UserField(required=False)
    modified_by = UserField(required=False)
    priority = BarrierPriorityField(required=False)
    priority_level = serializers.CharField(required=False)
    main_sector = SectorField(required=False)
    sectors = SectorsField(required=False)
    source = SourceField(required=False)
    status = StatusField(required=False)
    sub_status = SubStatusField(required=False, allow_blank=True)
    public_barrier = NestedPublicBarrierSerializer(required=False)
    public_eligibility = PublicEligibilityField(required=False)
    term = TermField(required=False, allow_null=True)
    tags = TagsField(required=False)
    title = serializers.CharField(required=False)
    trade_category = TradeCategoryField(required=False)
    trade_direction = TradeDirectionField(required=False)
    trading_bloc = TradingBlocField(required=False, allow_blank=True)
    unarchived_by = UserField(required=False)
    wto_profile = WTOProfileField(required=False)
    government_organisations = OrganisationsField(required=False)
    progress_updates = ProgressUpdateSerializer(required=False, many=True)
    programme_fund_progress_updates = ProgrammeFundProgressUpdateSerializer(
        required=False, many=True
    )
    is_top_priority = serializers.BooleanField(required=False)
    export_types = ExportTypesField(required=False)
    last_seen_on = serializers.SerializerMethodField()
    next_steps_items = serializers.SerializerMethodField()

    class Meta:
        model = Barrier
        read_only_fields = (
            "archived_by",
            "archived_on",
            "code",
            "created_by",
            "created_on",
            "id",
            "is_top_priority",
            "last_seen_on",
            "location",
            "modified_by",
            "modified_on",
            "priority_date",
            "economic_assessments",
            "valuation_assessments",
            "resolvability_assessments",
            "strategic_assessments",
            "unarchived_by",
            "unarchived_on",
            "progress_updates",
            "next_steps_items",
        )

    def get_last_seen_on(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            hit, _ = BarrierUserHit.objects.get_or_create(
                user=request.user, barrier=obj
            )
            return hit.last_seen

    def get_next_steps_items(self, instance):
        next_steps = instance.next_steps_items.all().order_by(
            "-status", "completion_date"
        )
        return NextStepItemSerializer(next_steps, required=False, many=True).data

    def validate_public_eligibility(self, attrs):
        """Check for permissions here"""
        # TODO: check user permissions - this field should only be updated
        #       by the publishing team
        return attrs

    def validate_public_eligibility_summary(self, attrs):
        """Check for permissions here"""
        # TODO: check user permissions - this field should only be updated
        #       by the publishing team
        return attrs
