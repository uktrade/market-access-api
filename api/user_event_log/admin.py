import json

from django.contrib import admin
from django.utils.html import format_html

from api.user_event_log.models import UserEvent


@admin.register(UserEvent)
class UserEventAdmin(admin.ModelAdmin):
    """Admin configuration for UserEvent."""

    list_display = ("timestamp", "user", "type", "api_url_path")
    list_filter = ("type", "api_url_path")
    list_select_related = ("user",)
    fields = (
        "id",
        "timestamp",
        "username",
        "type",
        "api_url_path",
        "pretty_data",
    )
    readonly_fields = fields

    def username(self, obj):
        """Returns a link to the adviser."""
        return obj.user.username

    username.short_description = "user"

    def pretty_data(self, obj):
        """Returns the data field formatted with indentation."""
        return format_html("<pre>{0}</pre>", json.dumps(obj.data, indent=2))

    pretty_data.short_description = "data"
