from rest_framework import serializers


class LocationFieldMixin(metaclass=serializers.SerializerMetaclass):
    # Use metaclass to get the fields registered at the serializer where the mixin is used
    # The field will need to be listed on the serializer using this mixin
    location = serializers.SerializerMethodField()

    def get_location(self, obj):
        try:
            return obj.location or ""
        except AttributeError:
            return ""


class EconomicAssessmentRatingFieldMixin(metaclass=serializers.SerializerMetaclass):
    economic_assessment_rating = serializers.SerializerMethodField()

    def get_economic_assessment_rating(self, obj):
        assessment = obj.current_economic_assessment
        if assessment:
            return assessment.get_rating_display()


class EconomicAssessmentExplanationFieldMixin(
    metaclass=serializers.SerializerMetaclass
):
    economic_assessment_explanation = serializers.SerializerMethodField()

    def get_economic_assessment_explanation(self, obj):
        assessment = obj.current_economic_assessment
        if assessment:
            return assessment.explanation


class ValueToEconomyFieldMixin(metaclass=serializers.SerializerMetaclass):
    """Value of UK exports of affected goods to partner country"""

    value_to_economy = serializers.SerializerMethodField()

    def get_value_to_economy(self, obj):
        assessment = obj.current_economic_assessment
        if assessment:
            return assessment.export_potential.get("uk_exports_affected")


class ImportMarketSizeFieldMixin(metaclass=serializers.SerializerMetaclass):
    import_market_size = serializers.SerializerMethodField()

    def get_import_market_size(self, obj):
        """Size of import market for affected product(s)"""
        assessment = obj.current_economic_assessment
        if assessment:
            return assessment.export_potential.get("import_market_size")


class ValuationAssessmentRatingFieldMixin(metaclass=serializers.SerializerMetaclass):
    valuation_assessment_rating = serializers.SerializerMethodField()

    def get_valuation_assessment_rating(self, obj):
        latest_valuation_assessment = obj.current_valuation_assessment
        if latest_valuation_assessment:
            return latest_valuation_assessment.rating


class ValuationAssessmentExplanationFieldMixin(
    metaclass=serializers.SerializerMetaclass
):
    valuation_assessment_explanation = serializers.SerializerMethodField()

    def get_valuation_assessment_explanation(self, obj):
        latest_valuation_assessment = obj.current_valuation_assessment
        if latest_valuation_assessment:
            return latest_valuation_assessment.explanation


class AssessmentFieldsMixin(
    EconomicAssessmentRatingFieldMixin,
    EconomicAssessmentExplanationFieldMixin,
    ValueToEconomyFieldMixin,
    ImportMarketSizeFieldMixin,
    ValuationAssessmentRatingFieldMixin,
    ValuationAssessmentExplanationFieldMixin,
):
    pass
