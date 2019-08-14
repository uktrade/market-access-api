from uuid import uuid4

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver

from api.core.models import ArchivableModel


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Profile(models.Model):
    """
    Profile object to hold user profile elements (temporary)
    This will be replaced by external SSO profile
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    location = models.UUIDField(null=True, blank=True)
    internal = models.BooleanField(default=False)
    user_profile = JSONField(
        null=True, help_text="temporary field to hold sso profile json object"
    )
    sso_user_id = models.UUIDField(
        null=True, help_text="Staff SSO UUID for reference"
    )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create profile object if it doesn't already exist
    upon user object creation
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """
    Create profile object if it doesn't already exist
    otherwise save it
    """
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
