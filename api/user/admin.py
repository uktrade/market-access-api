from django import forms
from django.contrib import admin

from api.user.models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        widgets = {"location": forms.Select()}
        fields = "__all__"


class ProfileAdmin(admin.ModelAdmin):
    """
    ModelAdmin class for customised behaviour for
    allowing User Profile edits.
    """

    def has_delete_permission(self, request, obj=None):
        """No Delete permission"""
        return False

    list_display = ("user", "location", "internal")


admin.site.register(Profile, ProfileAdmin)
