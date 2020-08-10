import datetime
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import Q, CASCADE
from django.utils import timezone

from simple_history.models import HistoricalRecords

from api.core.exceptions import ArchivingException
from api.metadata.constants import (
    BarrierStatus,
    BARRIER_ARCHIVED_REASON,
    BARRIER_SOURCE,
    BARRIER_PENDING,
    PROBLEM_STATUS_TYPES,
    STAGE_STATUS,
    TRADE_DIRECTION_CHOICES,
    PublicBarrierStatus,
)
from api.commodities.models import Commodity
from api.core.models import BaseModel, FullyArchivableMixin
from api.metadata.models import BarrierPriority, BarrierTag, Category
from api.barriers import validators
from api.barriers.report_stages import REPORT_CONDITIONS, report_stage_status
from api.barriers.utils import random_barrier_reference

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Stage(models.Model):
    """ Reporting workflow stages  """

    code = models.CharField(max_length=4, null=False)
    description = models.CharField(max_length=MAX_LENGTH)
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.code


class ReportManager(models.Manager):
    """ Manage reports within the model, with draft=True """

    def get_queryset(self):
        return super().get_queryset().filter(Q(draft=True) & Q(archived=False))


class BarrierManager(models.Manager):
    """
    Manage barriers within the model, with draft=False
    Keep archived filter off from here to allow to filter for archived barriers only.
    """

    def get_queryset(self):
        return super().get_queryset().filter(draft=False)


class BarrierHistoricalModel(models.Model):
    """
    Abstract model for history models tracking category changes.
    """
    categories_cache = ArrayField(
        models.CharField(max_length=20),
        blank=True,
        null=True,
        default=list,
    )
    commodities_cache = ArrayField(JSONField(), default=list)
    tags_cache = ArrayField(
        models.IntegerField(),
        null=True,
        default=list,
    )

    def get_changed_fields(self, old_history):
        changed_fields = set(self.diff_against(old_history).changed_fields)

        if set(self.categories_cache or []) != set(old_history.categories_cache or []):
            changed_fields.add("categories")

        commodity_codes = [c.get("code") for c in self.commodities_cache]
        old_commodity_codes = [c.get("code") for c in old_history.commodities_cache]
        if set(commodity_codes) != set(old_commodity_codes):
            changed_fields.add("commodities")

        if set(self.tags_cache or []) != set(old_history.tags_cache or []):
            changed_fields.add("tags")

        if changed_fields.intersection(("export_country", "country_admin_areas")):
            changed_fields.discard("export_country")
            changed_fields.discard("country_admin_areas")
            changed_fields.add("location")

        if "all_sectors" in changed_fields:
            changed_fields.discard("all_sectors")
            changed_fields.add("sectors")

        return list(changed_fields)

    def update_categories(self):
        self.categories_cache = list(
            self.instance.categories.values_list("id", flat=True)
        )

    def update_commodities(self):
        self.commodities_cache = [
            {
                "code": barrier_commodity.code,
                "country": {"id": str(barrier_commodity.country)},
                "commodity": {
                    "code": barrier_commodity.commodity.code,
                    "description": barrier_commodity.commodity.description,
                    "full_description": barrier_commodity.commodity.full_description,
                    "version": barrier_commodity.commodity.version,
                }
            }
            for barrier_commodity in self.instance.barrier_commodities.all()
        ]

    def update_tags(self):
        self.tags_cache = list(self.instance.tags.values_list("id", flat=True))

    def save(self, *args, **kwargs):
        self.update_categories()
        self.update_commodities()
        self.update_tags()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class BarrierInstance(FullyArchivableMixin, BaseModel):
    """ Barrier Instance, converted from a completed and accepted Report """

    id = models.UUIDField(primary_key=True, default=uuid4)
    code = models.CharField(
        max_length=MAX_LENGTH,
        null=True,
        unique=True,
        help_text="readable reference code",
        db_index=True,
    )
    problem_status = models.PositiveIntegerField(
        choices=PROBLEM_STATUS_TYPES,
        null=True,
        help_text="type of problem, long term or short term",
    )
    end_date = models.DateField(null=True, help_text="Date the barrier ends")

    export_country = models.UUIDField(null=True)
    country_admin_areas = ArrayField(
        models.UUIDField(),
        blank=True,
        default=list,
        help_text="list of states, provinces, regions etc within a country",
    )
    trade_direction = models.SmallIntegerField(
        choices=TRADE_DIRECTION_CHOICES,
        blank=False,
        null=True,
        default=None
    )

    sectors_affected = models.NullBooleanField(
        help_text="boolean to signify one or more sectors are affected by this barrier"
    )
    all_sectors = models.NullBooleanField(
        help_text="boolean to signify that all sectors are affected by this barrier"
    )
    sectors = ArrayField(
        models.UUIDField(),
        blank=True,
        null=False,
        default=list,
        help_text="list of sectors that are affected",
    )
    companies = JSONField(
        null=True, default=None, help_text="list of companies that are affected"
    )

    product = models.CharField(max_length=MAX_LENGTH, null=True)
    source = models.CharField(
        choices=BARRIER_SOURCE, max_length=25, null=True, help_text="chance of success"
    )
    other_source = models.CharField(max_length=MAX_LENGTH, null=True)
    barrier_title = models.CharField(max_length=MAX_LENGTH, null=True)
    summary = models.TextField(null=True)
    is_summary_sensitive = models.NullBooleanField(
        help_text="Does the summary contain sensitive information"
    )
    # next steps will be saved here momentarily during reporting.
    # once the report is ready for submission, this will be added as a new note
    next_steps_summary = models.TextField(null=True)

    categories = models.ManyToManyField(
        Category, related_name="barriers", help_text="Barrier categories"
    )

    reported_on = models.DateTimeField(db_index=True, auto_now_add=True)

    # Barrier status
    status = models.PositiveIntegerField(
        choices=BarrierStatus.choices, default=0, help_text="status of the barrier instance"
    )
    sub_status = models.CharField(
        choices=BARRIER_PENDING,
        max_length=25,
        null=True,
        default=None,
        help_text="barrier sub status",
    )
    sub_status_other = models.CharField(
        max_length=MAX_LENGTH,
        null=True,
        help_text="barrier sub status text for other choice"
    )
    status_summary = models.TextField(
        null=True, default=None, help_text="status summary if provided by user"
    )
    status_date = models.DateField(
        null=True, help_text="date when status action occurred"
    )
    public_eligibility = models.BooleanField(
        default=None, null=True, help_text="Mark the barrier as either publishable or unpublishable to the public."
    )
    public_eligibility_summary = models.TextField(
        blank=True, help_text="Public eligibility summary if provided by user."
    )

    # Barrier priority
    priority = models.ForeignKey(
        BarrierPriority,
        default=1,
        related_name="barrier",
        on_delete=models.PROTECT,
    )
    priority_summary = models.TextField(
        null=True, default=None, help_text="priority summary if provided by user"
    )
    priority_date = models.DateTimeField(
        auto_now=True, null=True, help_text="date when priority was set"
    )
    stages = models.ManyToManyField(
        Stage,
        related_name="report_stages",
        through="BarrierReportStage",
        help_text="Store reporting stages before submitting",
    )
    archived_reason = models.CharField(
        choices=BARRIER_ARCHIVED_REASON, max_length=25, null=True
    )
    archived_explanation = models.TextField(blank=True, null=True)
    wto_profile = models.OneToOneField(
        "wto.WTOProfile",
        null=True,
        related_name="barrier",
        on_delete=models.SET_NULL,
    )
    commodities = models.ManyToManyField(Commodity, through="BarrierCommodity")
    draft = models.BooleanField(default=True)

    history = HistoricalRecords(bases=[BarrierHistoricalModel])

    tags = models.ManyToManyField(BarrierTag)

    def __str__(self):
        if self.barrier_title is None:
            return self.code
        return self.barrier_title

    objects = models.Manager()
    reports = ReportManager()
    barriers = BarrierManager()

    class Meta:
        ordering = ["-reported_on"]
        permissions = [
            ('change_barrier_public_eligibility', 'Can change barrier public eligibility'),
        ]

    def current_progress(self):
        """ checks current dataset to see how far reporting workflow is done """
        progress_list = []
        for stage in REPORT_CONDITIONS:
            stage_code, status = report_stage_status(self, stage)
            progress_list.append((Stage.objects.get(code=stage_code), status))

        return progress_list

    def submit_report(self, submitted_by=None):
        """ submit a report, convert it into a barrier """
        for validator in [validators.ReportReadyForSubmitValidator()]:
            validator.set_instance(self)
            validator()

        if not self.status_date:
            self.status_date = timezone.now()

        self.modified_by = submitted_by
        self.reported_on = timezone.now()
        self.draft = False
        self.save()
        self.progress.all().delete()
        return self

    @property
    def archived_user(self):
        return self._cleansed_username(self.archived_by)

    @property
    def unarchived_user(self):
        return self._cleansed_username(self.unarchived_by)

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)

    @property
    def has_assessment(self):
        return hasattr(self, 'assessment')

    def last_seen_by(self, user_id):
        try:
            hit = BarrierUserHit.objects.get(user=user_id, barrier=self)
            return hit.last_seen
        except BarrierUserHit.DoesNotExist:
            return None

    def archive(self, user, reason=None, explanation=None):
        try:
            if self.public_barrier.public_view_status == PublicBarrierStatus.PUBLISHED:
                raise ArchivingException("Public barrier should be unpublished first.")
        except PublicBarrier.DoesNotExist:
            pass
        self.archived_explanation = explanation
        self.unarchived_by = None
        self.unarchived_on = None
        self.unarchived_reason = ""
        super().archive(user, reason)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        """
        Upon creating new item, generate a readable reference code
        """
        if self.code is None:
            loop_num = 0
            unique = False
            while not unique:
                if loop_num < settings.REF_CODE_MAX_TRIES:
                    new_code = random_barrier_reference()
                    if not BarrierInstance.objects.filter(code=new_code):
                        self.code = new_code
                        unique = True
                    loop_num += 1
                else:
                    raise ValueError("Error generating a unique reference code.")

        if self.source != BARRIER_SOURCE.OTHER:
            self.other_source = None

        super(BarrierInstance, self).save(
            force_insert, force_update, using, update_fields
        )


class PublicBarrierHistoricalModel(models.Model):
    """
    Abstract model for tracking m2m changes for PublicBarrier.
    """
    categories_cache = ArrayField(
        models.CharField(max_length=20),
        blank=True,
        null=True,
        default=list,
    )

    def get_changed_fields(self, old_history):
        changed_fields = set(self.diff_against(old_history).changed_fields)

        if set(self.categories_cache or []) != set(old_history.categories_cache or []):
            changed_fields.add("categories")

        if "all_sectors" in changed_fields:
            changed_fields.discard("all_sectors")
            changed_fields.add("sectors")

        if "_title" in changed_fields:
            changed_fields.discard("_title")
            changed_fields.add("title")

        if "_summary" in changed_fields:
            changed_fields.discard("_summary")
            changed_fields.add("summary")

        if "_public_view_status" in changed_fields:
            changed_fields.discard("_public_view_status")
            changed_fields.add("public_view_status")

        return list(changed_fields)

    def update_categories(self):
        self.categories_cache = list(
            self.instance.categories.values_list("id", flat=True)
        )

    @property
    def public_view_status(self):
        return self._public_view_status

    @property
    def summary(self):
        return self._summary

    @property
    def title(self):
        return self._title

    def save(self, *args, **kwargs):
        self.update_categories()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class PublicBarrier(FullyArchivableMixin, BaseModel):
    """
    Public barriers are the representation of a barrier (as the name suggests) to the public.
    This table should not be exposed to the public however only to the DMAS frontend which requires login.
    Transfer the data to a flat file or another service which can safely expose the data.
    """
    barrier = models.OneToOneField(BarrierInstance, on_delete=CASCADE, related_name="public_barrier")

    # === Title related fields =====
    _title = models.CharField(null=True, max_length=MAX_LENGTH)
    title_updated_on = models.DateTimeField(null=True, blank=True)
    internal_title_at_update = models.CharField(null=True, max_length=MAX_LENGTH)

    # === Summary related fields =====
    _summary = models.TextField(null=True)
    summary_updated_on = models.DateTimeField(null=True, blank=True)
    internal_summary_at_update = models.TextField(null=True, max_length=MAX_LENGTH)

    # === Non editable fields ====
    status = models.PositiveIntegerField(choices=BarrierStatus.choices, default=0)
    country = models.UUIDField()
    sectors = ArrayField(models.UUIDField(), blank=True, null=False, default=list)
    all_sectors = models.NullBooleanField()
    categories = models.ManyToManyField(Category, related_name="public_barriers")

    published_versions = JSONField(default=dict)

    # === Status and timestamps ====
    _public_view_status = models.PositiveIntegerField(choices=PublicBarrierStatus.choices, default=0)
    first_published_on = models.DateTimeField(null=True, blank=True)
    last_published_on = models.DateTimeField(null=True, blank=True)
    unpublished_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        permissions = [
            ('publish_barrier', 'Can publish barrier'),
            ('mark_barrier_as_ready_for_publishing', 'Can mark barrier as ready for publishing'),
        ]

    def add_new_version(self):
        # self.published_versions structure:
        # {
        #     "latest_version": 3,
        #     "versions": {
        #         1: {
        #                "version": 1,
        #                "published_on: "datetime",
        #            },
        #         2: {...},
        #         3: {...}
        #     }
        # }
        latest_version = self.published_versions.get("latest_version", "0")
        new_version = str(int(latest_version) + 1)
        entry = {
            "version": new_version,
            "published_on": self.last_published_on.isoformat()
        }
        if not self.published_versions:
            self.published_versions = {"latest_version": "0", "versions": {}}
        self.published_versions["latest_version"] = new_version
        self.published_versions["versions"].setdefault(new_version, entry)

    def get_published_version(self, version):
        version = str(version)
        if self.published_versions:
            timestamp = self.published_versions["versions"][version]["published_on"]
            historic_public_barrier = self.history.as_of(datetime.datetime.fromisoformat(timestamp))
            return historic_public_barrier
        else:
            return None

    @property
    def latest_published_version(self):
        return self.get_published_version(self.published_versions.get("latest_version", 0))

    def update_non_editable_fields(self):
        self.status = self.internal_status
        self.country = self.internal_country
        self.sectors = self.internal_sectors
        self.all_sectors = self.internal_all_sectors
        self.categories.set(self.internal_categories.all())

    def publish(self):
        if self.ready_to_be_published:
            self.update_non_editable_fields()
            self.unpublished_on = None
            self.public_view_status = PublicBarrierStatus.PUBLISHED
            self.add_new_version()
            self._history_date = self.last_published_on
            self.save()
            return True
        else:
            return False

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value
        self.internal_title_at_update = self.barrier.barrier_title
        self.title_updated_on = datetime.datetime.now()

    @property
    def title_changed(self):
        if self.title:
            if self.latest_published_version:
                return self.title != self.latest_published_version.title
            else:
                return True
        else:
            return False

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, value):
        self._summary = value
        self.internal_summary_at_update = self.barrier.summary
        self.summary_updated_on = datetime.datetime.now()

    @property
    def summary_changed(self):
        if self.summary:
            if self.latest_published_version:
                return self.summary != self.latest_published_version.summary
            else:
                return True
        else:
            return False

    @property
    def public_view_status(self):
        # set default if eligibility is avail on the internal barrier
        if (self._public_view_status == PublicBarrierStatus.UNKNOWN):
            if self.barrier.public_eligibility is True:
                self._public_view_status = PublicBarrierStatus.ELIGIBLE
            if self.barrier.public_eligibility is False:
                self._public_view_status = PublicBarrierStatus.INELIGIBLE

        # The internal barrier might get withdrawn from the public domain
        # in which case it will be marked as ineligible for public view
        # and the public barrier view status should update as well
        #
        # Note: cannot automatically change from published
        #       the public barrier would need to be unpublished first
        if self._public_view_status != PublicBarrierStatus.PUBLISHED:
            # Marking the public barrier ineligible
            if (
                self.barrier.public_eligibility is False
                and self._public_view_status != PublicBarrierStatus.INELIGIBLE
            ):
                self._public_view_status = PublicBarrierStatus.INELIGIBLE
                self.save()
            # Marking the public barrier eligible
            if (
                self.barrier.public_eligibility is True
                and self._public_view_status == PublicBarrierStatus.INELIGIBLE
            ):
                self._public_view_status = PublicBarrierStatus.ELIGIBLE
                self.save()

        return self._public_view_status

    @public_view_status.setter
    def public_view_status(self, value):
        """ Set relevant date automatically """
        status = int(value)
        self._public_view_status = status
        # auto update date fields based on the new status
        now = datetime.datetime.now()
        if status == PublicBarrierStatus.PUBLISHED:
            self.first_published_on = self.first_published_on or now
            self.last_published_on = now
        if status == PublicBarrierStatus.UNPUBLISHED:
            self.unpublished_on = now

    @property
    def internal_title_changed(self):
        if self.internal_title_at_update:
            return self.barrier.barrier_title != self.internal_title_at_update
        else:
            return False

    @property
    def internal_summary_changed(self):
        if self.internal_summary_at_update:
            return self.barrier.summary != self.internal_summary_at_update
        else:
            return False

    @property
    def internal_status(self):
        return self.barrier.status

    @property
    def internal_status_changed(self):
        return self.barrier.status != self.status

    @property
    def internal_country(self):
        return self.barrier.export_country

    @property
    def internal_country_changed(self):
        return self.barrier.export_country != self.country

    @property
    def internal_sectors(self):
        return self.barrier.sectors

    @property
    def internal_sectors_changed(self):
        return self.barrier.sectors != self.sectors

    @property
    def internal_all_sectors(self):
        return self.barrier.all_sectors

    @property
    def internal_all_sectors_changed(self):
        return self.barrier.all_sectors != self.all_sectors

    @property
    def internal_categories(self):
        return self.barrier.categories

    @property
    def internal_categories_changed(self):
        # TODO: consider other options
        return set(self.barrier.categories.all()) != set(self.categories.all())

    @property
    def ready_to_be_published(self):
        is_ready = self.public_view_status == PublicBarrierStatus.READY
        is_republish = self.unpublished_on is not None
        has_changes = self.unpublished_changes
        has_title_and_summary = bool(self.title and self.summary)
        return (
            is_ready
            and has_title_and_summary
            and (is_republish or has_changes)
        )

    @property
    def unpublished_changes(self):
        return (
            self.title_changed
            or self.summary_changed
            or self.internal_status_changed
            or self.internal_country_changed
            or self.internal_sectors_changed
            or self.internal_all_sectors_changed
            or self.internal_sectors_changed
            or self.internal_categories_changed
        )

    history = HistoricalRecords(bases=[PublicBarrierHistoricalModel])


class BarrierUserHit(models.Model):
    """Record when a user has most recently seen a barrier."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    barrier = models.ForeignKey(BarrierInstance, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'barrier']


class BarrierReportStage(BaseModel):
    """ Many to Many between report and workflow stage """

    barrier = models.ForeignKey(
        BarrierInstance, related_name="progress", on_delete=models.CASCADE
    )
    stage = models.ForeignKey(Stage, related_name="progress", on_delete=models.CASCADE)
    status = models.PositiveIntegerField(choices=STAGE_STATUS, null=True)

    history = HistoricalRecords()

    class Meta:
        unique_together = (("barrier", "stage"),)


class BarrierCommodity(models.Model):
    barrier = models.ForeignKey(BarrierInstance, related_name="barrier_commodities", on_delete=models.CASCADE)
    commodity = models.ForeignKey(Commodity, related_name="barrier_commodities", on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    country = models.UUIDField()
    created_on = models.DateTimeField(auto_now_add=True)
