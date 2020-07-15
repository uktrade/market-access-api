from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import Q
from django.utils import timezone

from simple_history.models import HistoricalRecords

from api.metadata.constants import (
    BARRIER_STATUS,
    BARRIER_SOURCE,
    BARRIER_PENDING,
    PROBLEM_STATUS_TYPES,
    STAGE_STATUS,
    TRADE_DIRECTION_CHOICES
)

from api.core.models import BaseModel, FullyArchivableMixin
from api.metadata.models import BarrierPriority, BarrierTag, Category, HSCode
from api.barriers import validators
from api.barriers.report_stages import REPORT_CONDITIONS, report_stage_status
from api.barriers.utils import random_barrier_reference
from api.metadata.constants import BARRIER_ARCHIVED_REASON

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
    tags_cache = ArrayField(
        models.IntegerField(),
        null=True,
        default=list,
    )

    def get_changed_fields(self, old_history):
        changed_fields = set(self.diff_against(old_history).changed_fields)

        if set(self.categories_cache or []) != set(old_history.categories_cache or []):
            changed_fields.add("categories")

        if set(self.tags_cache or []) != set(old_history.tags_cache or []):
            changed_fields.add("tags")

        if changed_fields.intersection(("export_country", "country_admin_areas")):
            changed_fields.discard("export_country")
            changed_fields.discard("country_admin_areas")
            changed_fields.add("location")

        return list(changed_fields)

    def update_categories(self):
        self.categories_cache = list(
            self.instance.categories.values_list("id", flat=True)
        )

    def update_tags(self):
        self.tags_cache = list(self.instance.tags.values_list("id", flat=True))

    def save(self, *args, **kwargs):
        self.update_categories()
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
        null=True,
        default=None,
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
        choices=BARRIER_STATUS, default=0, help_text="status of the barrier instance"
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

    # Barrier priority
    priority = models.ForeignKey(
        BarrierPriority,
        null=True,
        default=None,
        related_name="barrier_priority",
        on_delete=models.SET_NULL,
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
    hs_codes = models.ManyToManyField(HSCode)
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
