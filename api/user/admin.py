from django import forms
from django.contrib import admin

from api.user.models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        widgets = {
            'location': forms.Select(),
        }
        fields = '__all__'


class ProfileAdmin(admin.ModelAdmin):
    """
    ModelAdmin class for customised behaviour for
    allowing User Profile edits.
    """
    # form = ProfileForm

    # def formfield_for_dbfield(self, db_field, **kwargs):
    #     # Add some logic here to base your choices on.
    #     if db_field.name == 'location':
    #         kwargs['location'].choices = (
    #             ('ba6ee1ca-5d95-e211-a939-e4115bead28a', 'South Korea'),
    #             ('7c6a9ab2-5d95-e211-a939-e4115bead28a', 'Japan'),
    #         )
    #     return super(ProfileAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    # def formfield_for_choice_field(self, db_field, request, **kwargs):
    #     if db_field.name == "location":
    #         kwargs['choices'] = (
    #             ('ba6ee1ca5d95e211a939e4115bead28a', 'South Korea'),
    #             ('7c6a9ab2-5d95-e211-a939-e4115bead28a', 'Japan'),
    #         )
    #     return super(ProfileAdmin, self).formfield_for_choice_field(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        """ No Delete permission """
        return False

    list_display = ('user', 'location', 'internal')

admin.site.register(Profile, ProfileAdmin)
