from django.contrib import admin

from .models import Barrier


class BarrierAdmin(admin.ModelAdmin):
    """
    ModelAdmin class for customised behaviour for
    allowing Barrier archivable.
    Admin shouldn't be able to add or delete objects
    """

    def has_add_permission(self, request, obj=None):
        """ No Add permission """
        return False

    def has_delete_permission(self, request, obj=None):
        """ No Delete permission """
        return False

    list_display = ("id", "code", "reported_on", "archived")
    search_fields = ("id", "code")
    list_filter = ("reported_on",)
    date_hierarchy = "reported_on"
    ordering = ("-reported_on",)
    fields = ("archived", "archived_on", "archived_reason", "archived_by")


admin.site.register(Barrier, BarrierAdmin)
