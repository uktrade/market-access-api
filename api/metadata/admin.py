from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin

from api.metadata.models import BarrierTag, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    ModelAdmin class for customised behaviour for
    allowing Category edits.
    """
    list_display = ("title", "category")


@admin.register(BarrierTag)
class BarrierTagAdmin(OrderedModelAdmin):
    fields = ("title", "description", "show_at_reporting")
    list_display = (
        "title",
        "description",
        "show_at_reporting",
        "created_by",
        "modified_on",
        "order",
        'move_up_down_links',
    )
