from uuid import uuid4

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver

from api.core.models import ArchivableModel


MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Watchlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=MAX_LENGTH, null=False)
    filter = JSONField(
        null=False, help_text="list of filters that make up this watchlist"
    )


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    location = models.UUIDField(null=True, blank=True)
    internal = models.BooleanField(default=False)
    watchlists = models.ManyToManyField(
        Watchlist, related_name="watchlists", help_text="personalised watch lists"
    )



@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
