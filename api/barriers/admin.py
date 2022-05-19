from django.contrib import admin

from .models import Barrier, PublicBarrier


class BarrierAdmin(admin.ModelAdmin):
    """
    ModelAdmin class for customised behaviour for
    allowing Barrier archivable.
    Admin shouldn't be able to add or delete objects
    """

    def has_add_permission(self, request, obj=None):
        """No Add permission"""
        return False

    def has_delete_permission(self, request, obj=None):
        """No Delete permission"""
        return False

    list_display = (
        "title",
        "id",
        "code",
        "reported_on",
        "archived",
        "top_priority_status",
    )
    search_fields = (
        "id",
        "code",
        "tags",
        "top_priority_status",
    )
    list_filter = (
        "reported_on",
        "tags",
        "top_priority_status",
    )
    date_hierarchy = "reported_on"
    ordering = ("-reported_on",)
    fields = (
        "archived",
        "archived_on",
        "archived_reason",
        "archived_by",
        "top_priority_status",
        "tags",
    )


admin.site.register(Barrier, BarrierAdmin)


class PublicBarrierAdmin(admin.ModelAdmin):
    list_display = ("id", "barrier", "country", "status")


admin.site.register(PublicBarrier, PublicBarrierAdmin)
