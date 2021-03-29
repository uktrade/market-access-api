from django.contrib import admin

from .models import ExcludeFromNotification, Mention


@admin.register(Mention)
class MentionAdmin(admin.ModelAdmin):
    list_display = ("barrier", "created_on", "email_used", "recipient")


@admin.register(ExcludeFromNotification)
class ExcludeFromNotificationAdmin(admin.ModelAdmin):
    list_display = ("excluded_user", "exclude_email")
