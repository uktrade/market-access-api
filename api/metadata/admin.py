from django.contrib import admin

from api.metadata.models import BarrierType

class BarrierTypeAdmin(admin.ModelAdmin):
    """
    ModelAdmin class for customised behaviour for
    allowing BarrierType edits.
    """

    list_display = ('title', 'category')

admin.site.register(BarrierType, BarrierTypeAdmin)
