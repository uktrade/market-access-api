import logging
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_filters import BaseInFilter

from api.barriers import models as barriers_models
from api.core.utils import nested_sort
from api.metadata import models as metadata_models
from api.metadata.constants import TRADING_BLOC_CHOICES
from api.user.constants import USER_ACTIVITY_EVENT_TYPES

logger = logging.getLogger(__name__)

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Profile(models.Model):
    """
    Profile object to hold user profile elements (temporary)
    This will be replaced by external SSO profile
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    location = models.UUIDField(null=True, blank=True)
    internal = models.BooleanField(default=False)
    user_profile = models.JSONField(
        blank=True,
        null=True,
        help_text="temporary field to hold sso profile json object",
    )
    sso_user_id = models.UUIDField(
        blank=True,
        null=True,
        help_text="Legacy Staff SSO UUID for reference",
    )
    sso_email_user_id = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        help_text="Canonical Staff SSO UUID for reference",
    )
    last_activity = models.DateTimeField(null=True, blank=True)
    policy_teams = models.ManyToManyField(
        metadata_models.PolicyTeam,
        blank=True,
        null=True,
        help_text="Policy teams that the user is interested in",
    )
    sectors = ArrayField(
        models.UUIDField(),
        blank=True,
        default=list,
        help_text="Sectors that the user is interested in",
    )
    organisations = models.ManyToManyField(
        metadata_models.Organisation,
        blank=True,
        help_text="Organisations that the user is interested in",
    )
    countries = ArrayField(
        models.UUIDField(),
        blank=True,
        default=list,
        help_text="Countries that the user is interested in",
    )
    trading_blocs = ArrayField(
        models.CharField(max_length=7, blank=True, choices=TRADING_BLOC_CHOICES),
        blank=True,
        default=list,
        help_text="Trading blocs that the user is interested in",
    )
    overseas_regions = ArrayField(
        models.UUIDField(),
        blank=True,
        default=list,
        help_text="Overseas regions that the user is interested in",
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
    last_notified_barrier_ids = ArrayField(
        models.UUIDField(),
        blank=True,
        null=False,
        default=list,
    )
    last_notified_on = models.DateTimeField(auto_now_add=True)
    notify_about_additions = models.BooleanField(default=True)
    notify_about_updates = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    _barriers = None
    _new_barrier_ids = None
    _new_barriers_since_notified = None
    _updated_barrier_ids = None
    _updated_barriers_since_notified = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_filters = self.filters

    def are_api_parameters_equal(self, query_dict):
        ignore_keys = ("ordering", "limit", "offset", "search_id")
        query_dict = {k: v for k, v in query_dict.items() if k not in ignore_keys}
        filterset = barriers_models.BarrierFilterSet()

        for key, value in query_dict.items():
            if isinstance(filterset.filters.get(key), BaseInFilter):
                query_dict[key] = value.split(",")

        api_parameters = self.get_api_parameters()
        return nested_sort(query_dict) == nested_sort(api_parameters)

    def mark_as_notified(self, commit=True):
        self.last_notified_on = timezone.now()
        self.last_notified_barrier_ids = [barrier.id for barrier in self.barriers]
        if commit:
            self.save()

    def mark_as_seen(self):
        self.last_viewed_on = timezone.now()
        self.last_viewed_barrier_ids = [barrier.id for barrier in self.barriers]
        self.save()

    def get_api_parameters(self):
        params = {}

        for k, v in self.filters.items():
            if v == [""]:
                continue
            else:
                params[k] = v

        if "country" in params or "region" in params or "extra_location" in params:
            params["location"] = (
                params.pop("country", [])
                + params.pop("region", [])
                + params.pop("extra_location", [])
            )

        # Convert stored admin area filter to a simple list of values
        if "admin_areas" in params:
            admin_areas_filter_list = sum(params["admin_areas"].values(), [])

            if not admin_areas_filter_list:
                params.pop("admin_areas")
            else:
                params["admin_areas"] = admin_areas_filter_list

        params["archived"] = params.pop("only_archived", "0") or "0"
        return params

    @property
    def barriers(self):
        if self._barriers is None:
            filterset = barriers_models.BarrierFilterSet(user=self.user)
            barriers = barriers_models.Barrier.barriers.all()

            for name, value in self.get_api_parameters().items():
                filter = filterset.filters.get(name)

                if not filter:
                    continue

                barriers = filter.filter(barriers, value)

            self._barriers = barriers

        return self._barriers

    @property
    def barrier_count(self):
        return self.barriers.count()

    @property
    def new_barrier_ids(self):
        if self._new_barrier_ids is None:
            self._new_barrier_ids = list(
                self.barriers.filter(
                    modified_on__gt=self.last_viewed_on,
                )
                .exclude(
                    pk__in=self.last_viewed_barrier_ids,
                )
                .exclude(
                    modified_by=self.user,
                )
                .values_list("id", flat=True)
            )
        return self._new_barrier_ids

    @property
    def new_barrier_ids_since_notified(self):
        return [barrier.id for barrier in self.new_barriers_since_notified]

    @property
    def new_barriers_since_notified(self):
        if self._new_barriers_since_notified is None:
            self._new_barriers_since_notified = (
                self.barriers.filter(
                    modified_on__gt=self.last_notified_on,
                )
                .exclude(
                    pk__in=self.last_notified_barrier_ids,
                )
                .exclude(
                    modified_by=self.user,
                )
            )
        return self._new_barriers_since_notified

    @property
    def new_count(self):
        return len(self.new_barrier_ids)

    @property
    def new_count_since_notified(self):
        return len(self.new_barriers_since_notified)

    @property
    def updated_barrier_ids(self):
        if self._updated_barrier_ids is None:
            self._updated_barrier_ids = list(
                self.barriers.filter(
                    modified_on__gt=self.last_viewed_on,
                )
                .exclude(
                    pk__in=self.new_barrier_ids,
                )
                .exclude(
                    modified_by=self.user,
                )
                .values_list("id", flat=True)
            )
        return self._updated_barrier_ids

    @property
    def updated_barriers_since_notified(self):
        if self._updated_barriers_since_notified is None:
            self._updated_barriers_since_notified = (
                self.barriers.filter(
                    modified_on__gt=self.last_notified_on,
                )
                .exclude(
                    pk__in=self.new_barrier_ids_since_notified,
                )
                .exclude(
                    modified_by=self.user,
                )
            )
        return self._updated_barriers_since_notified

    @property
    def updated_count(self):
        return len(self.updated_barrier_ids)

    @property
    def updated_count_since_notified(self):
        return len(self.updated_barriers_since_notified)

    def should_notify(self):
        if self.notify_about_additions and self.new_count_since_notified > 0:
            return True
        if self.notify_about_updates and self.updated_count_since_notified > 0:
            return True
        return False

    def save(self, *args, **kwargs):
        if self._state.adding or self._original_filters != self.filters:
            self.mark_as_notified(commit=False)
            self._original_filters = self.filters
        super().save(*args, **kwargs)


class SavedSearch(BaseSavedSearch):
    name = models.CharField(max_length=MAX_LENGTH)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="saved_searches",
        on_delete=models.CASCADE,
    )
    filters = models.JSONField()

    class Meta:
        ordering = ("name",)


class MyBarriersSavedSearch(BaseSavedSearch):
    name = "Barriers I have created"
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
    name = "Barriers I own or am working on"
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


class UserActvitiyLog(models.Model):
    # nullable so audit trail stays after user is deleted
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    event_type = models.TextField(choices=USER_ACTIVITY_EVENT_TYPES)
    event_time = models.DateTimeField(auto_now_add=True)
    event_description = models.TextField(
        help_text="A human readable description of the event"
    )
    event_data = models.JSONField(
        blank=True,
        null=True,
        help_text="Field for extra event based data that is not covered by other fields",
    )

    class Meta:
        ordering = ("-event_time",)


# signal on login


def record_user_login_activity(sender, user, request, **kwargs):
    UserActvitiyLog.objects.create(
        user=user,
        event_type=USER_ACTIVITY_EVENT_TYPES.USER_LOGGED_IN,
        event_description="User logged in",
    )


user_logged_in.connect(record_user_login_activity)
