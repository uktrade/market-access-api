from django.contrib import admin

from api.metadata.models import BarrierTag, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    ModelAdmin class for customised behaviour for
    allowing Category edits.
    """
    list_display = ("title", "category")


@admin.register(BarrierTag)
class BarrierTagAdmin(admin.ModelAdmin):
    fields = ("title", "show_at_reporting")
    list_display = ("title", "show_at_reporting", "created_by", "modified_on")
