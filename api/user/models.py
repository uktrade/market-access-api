import datetime
from uuid import uuid4

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


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


class BaseSavedSearch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    last_viewed_barrier_ids = ArrayField(
        models.UUIDField(),
        blank=True,
        null=False,
        default=list,
    )
    last_viewed_on = models.DateTimeField(auto_now_add=True)
    created_on = models.DateTimeField(auto_now_add=True)

    _barriers = None

    class Meta:
        abstract = True

    def update_barriers(self, barriers):
        self.last_viewed_on = timezone.now()
        self.last_viewed_barrier_ids = [barrier["id"] for barrier in barriers]
        self.save()

    @property
    def barriers(self):
        # TODO: archived shouldn't always be False
        # TODO: fix circular imports
        if self._barriers is None:
            from api.barriers.views import BarrierFilterSet
            from api.barriers.models import BarrierInstance
            filterset = BarrierFilterSet(user=self.user)
            barriers = BarrierInstance.barriers.filter(archived=False)

            for name, value in self.filters.items():
                barriers = filterset.filters[name].filter(barriers, value)

            self._barriers = barriers
        return self._barriers

    @property
    def barrier_count(self):
        return self.barriers.count()

    @property
    def new_barrier_ids(self):
        barrier_ids = set(
            [barrier.id for barrier in self.barriers.exclude(created_by=self.user)]
        )
        new_barrier_ids = barrier_ids.difference(set(self.last_viewed_barrier_ids))
        return list(new_barrier_ids)

    @property
    def new_count(self):
        return len(self.new_barrier_ids)

    @property
    def updated_barrier_ids(self):
        # TODO: Include related model changes
        # TODO: Exclude changes this user has made
        updated_barrier_ids = []
        for barrier in self.barriers:
            if barrier.modified_on > self.last_viewed_on:
                updated_barrier_ids.append(barrier.id)
        return updated_barrier_ids

    @property
    def updated_count(self):
        return len(self.updated_barrier_ids)


class SavedSearch(BaseSavedSearch):
    name = models.CharField(max_length=MAX_LENGTH)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="saved_searches",
        on_delete=models.CASCADE,
    )
    filters = JSONField()


class MyBarriersSavedSearch(BaseSavedSearch):
    name = "My barriers"
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="my_barriers_saved_search",
        on_delete=models.CASCADE,
    )
    filters = {"user": "1"}


def get_my_barriers_saved_search(user):
    # TODO: Move to model? Use AutoOneToOneField?
    try:
        return user.my_barriers_saved_search
    except MyBarriersSavedSearch.DoesNotExist:
        return MyBarriersSavedSearch.objects.create(user=user)


class TeamBarriersSavedSearch(BaseSavedSearch):
    name = "Team barriers"
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="team_barriers_saved_search",
        on_delete=models.CASCADE,
    )
    filters = {"team": "1"}


def get_team_barriers_saved_search(user):
    # TODO: Move to model? Use AutoOneToOneField?
    try:
        return user.team_barriers_saved_search
    except TeamBarriersSavedSearch.DoesNotExist:
        return TeamBarriersSavedSearch.objects.create(user=user)


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
