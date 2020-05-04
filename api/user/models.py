from uuid import uuid4

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver


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


class SavedSearch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="saved_searches",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=MAX_LENGTH)
    filters = JSONField()
    last_viewed_barrier_ids = ArrayField(
        models.UUIDField(),
        blank=True,
        null=False,
        default=list,
    )
    last_viewed_on = models.DateTimeField()
    created_on = models.DateTimeField(auto_now_add=True)
    _barriers = None

    @property
    def barriers(self):
        # TODO: archived shouldn't always be False
        # TODO: fix circular imports
        if self._barriers is None:
            from api.barriers.views import BarrierFilterSet
            from api.barriers.models import BarrierInstance
            filterset = BarrierFilterSet()
            barriers = BarrierInstance.barriers.filter(archived=False)

            for name, value in self.filters.items():
                barriers = filterset.filters[name].filter(barriers, value)

            self._barriers = barriers
        return self._barriers

    @property
    def barrier_count(self):
        return self.barriers.count()

    @property
    def new_count(self):
        barrier_ids = set(
            [barrier.id for barrier in self.barriers.exclude(created_by=self.user)]
        )
        new_barrier_ids = barrier_ids.difference(set(self.last_viewed_barrier_ids))
        return len(new_barrier_ids)

    @property
    def updated_count(self):
        # TODO: Include related model changes
        # TODO: Exclude changes this user has made
        count = 0
        for barrier in self.barriers:
            if barrier.modified_on > self.last_viewed_on:
                count += 1
        return count


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
