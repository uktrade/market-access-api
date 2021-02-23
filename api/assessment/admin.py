from django.contrib import admin

from .models import (
    EconomicAssessment,
    EconomicImpactAssessment,
    EconomicAssessmentHistoricalModel,
    StrategicAssessment,
    ResolvabilityAssessment,
)


@admin.register(EconomicImpactAssessment)
class EconomicImpactAssessmentAdmin(admin.ModelAdmin):
    pass


@admin.register(EconomicAssessment)
class EconomicAssessmentAdmin(admin.ModelAdmin):
    pass


@admin.register(StrategicAssessment)
class StrategicAssessmentAdmin(admin.ModelAdmin):
    pass


@admin.register(ResolvabilityAssessment)
class ResolvabilityAssessmentAdmin(admin.ModelAdmin):
    pass
