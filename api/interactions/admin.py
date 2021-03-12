from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin

from .models import Mention


@admin.register(Mention)
class MentionAdmin(admin.ModelAdmin):
    list_display = ("barrier", "created_on", "email_used", "recipient")
