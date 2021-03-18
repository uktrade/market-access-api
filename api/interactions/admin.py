from django.contrib import admin

from .models import ExcludeFromNotifications, Mention


@admin.register(Mention)
class MentionAdmin(admin.ModelAdmin):
    list_display = ("barrier", "created_on", "email_used", "recipient")


@admin.register(ExcludeFromNotifications)
class ExcludeFromNotificationsAdmin(admin.ModelAdmin):
    list_display = ("excluded_user", "exclude_email")
