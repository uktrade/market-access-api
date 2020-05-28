import copy

from uuid import uuid4

from django_filters import BaseInFilter

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from api.barriers.filters import BarrierFilterSet
from api.barriers.models import BarrierInstance

from utils.tools import nested_sort

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
    notify_about_additions = models.BooleanField(default=False)
    notify_about_updates = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    _barriers = None
    _new_barrier_ids = None
    _updated_barrier_ids = None

    class Meta:
        abstract = True

    def are_api_parameters_equal(self, query_dict):
        ignore_keys = ('ordering', 'limit', 'offset', 'search_id')
        query_dict = {k: v for k, v in query_dict.items() if k not in ignore_keys}
        filterset = BarrierFilterSet()

        for key, value in query_dict.items():
            if isinstance(filterset.filters.get(key), BaseInFilter):
                query_dict[key] = value.split(",")

        api_parameters = self.get_api_parameters()
        return nested_sort(query_dict) == nested_sort(api_parameters)

    def mark_as_seen(self):
        self.last_viewed_on = timezone.now()
        self.last_viewed_barrier_ids = [barrier.id for barrier in self.barriers]
        self.save()

    def get_api_parameters(self):
        params = copy.deepcopy(self.filters)

        if "country" in params or "region" in params:
            params["location"] = params.pop("country", []) + params.pop("region", [])

        params["archived"] = params.pop("only_archived", "0") or "0"
        return params

    @property
    def barriers(self):
        if self._barriers is None:
            filterset = BarrierFilterSet(user=self.user)
            barriers = BarrierInstance.barriers.all()

            for name, value in self.get_api_parameters().items():
                barriers = filterset.filters[name].filter(barriers, value)

            self._barriers = barriers

        return self._barriers

    @property
    def barrier_count(self):
        return self.barriers.count()

    @property
    def new_barrier_ids(self):
        if self._new_barrier_ids is None:
            self._new_barrier_ids = []
            new_barriers = self.barriers.exclude(pk__in=self.last_viewed_barrier_ids)
            for barrier in new_barriers:
                if barrier.has_changes(
                    start_date=self.last_viewed_on,
                    exclude_user=self.user
                ):
                    self._new_barrier_ids.append(barrier.id)

        return self._new_barrier_ids

    @property
    def new_count(self):
        return len(self.new_barrier_ids)

    @property
    def updated_barrier_ids(self):
        if self._updated_barrier_ids is None:
            self._updated_barrier_ids = []
            for barrier in self.barriers:
                if barrier.has_changes(
                    start_date=self.last_viewed_on,
                    exclude_user=self.user
                ):
                    self._updated_barrier_ids.append(barrier.id)
        return self._updated_barrier_ids

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

    class Meta:
        ordering = ("name", )


class MyBarriersSavedSearch(BaseSavedSearch):
    name = "My barriers"
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="my_barriers_saved_search",
        on_delete=models.CASCADE,
    )
    filters = {"user": "1"}


def get_my_barriers_saved_search(user):
    try:
        return user.my_barriers_saved_search
    except MyBarriersSavedSearch.DoesNotExist:
        saved_search = MyBarriersSavedSearch.objects.create(user=user)
        saved_search.mark_as_seen()
        return saved_search


class TeamBarriersSavedSearch(BaseSavedSearch):
    name = "My team barriers"
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="team_barriers_saved_search",
        on_delete=models.CASCADE,
    )
    filters = {"team": "1"}


def get_team_barriers_saved_search(user):
    try:
        return user.team_barriers_saved_search
    except TeamBarriersSavedSearch.DoesNotExist:
        saved_search = TeamBarriersSavedSearch.objects.create(user=user)
        saved_search.mark_as_seen()
        return saved_search


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
