from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "satisfaction",
        "attempted_actions",
        "experienced_issues",
        "feedback_text",
        "created_on",
    )
