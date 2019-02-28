import datetime
from uuid import uuid4
from random import randrange

from django.conf import settings
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import Q
from django.utils import timezone

from simple_history.models import HistoricalRecords

from api.metadata.constants import (
    ADV_BOOLEAN,
    BARRIER_INTERACTION_TYPE,
    BARRIER_STATUS,
    BARRIER_SOURCE,
    BARRIER_TYPE_CATEGORIES,
    PROBLEM_STATUS_TYPES,
    STAGE_STATUS,
)
from api.core.models import ArchivableModel, BaseModel
from api.metadata.models import (
    BarrierType,
    BarrierPriority
)
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
    """ Manage reports within the model, with status 0 """

    def get_queryset(self):
        return (
            super(ReportManager, self)
            .get_queryset()
            .filter(Q(status=0) & Q(archived=False))
        )


class BarrierManager(models.Manager):
    """ Manage barriers within the model, with status not 0 """

    def get_queryset(self):
        return (
            super(BarrierManager, self)
            .get_queryset()
            .filter(~Q(status=0) & Q(archived=False))
        )


class BarrierInstance(BaseModel, ArchivableModel):
    """ Barrier Instance, converted from a completed and accepted Report """

    id = models.UUIDField(primary_key=True, default=uuid4)
    code = models.CharField(
        max_length=MAX_LENGTH,
        null=True,
        unique=True,
        help_text="readable reference code",
    )
    problem_status = models.PositiveIntegerField(
        choices=PROBLEM_STATUS_TYPES, null=True
    )

    is_resolved = models.NullBooleanField()
    resolved_date = models.DateField(null=True, default=None)

    export_country = models.UUIDField(null=True)

    sectors_affected = models.NullBooleanField()
    sectors = ArrayField(models.UUIDField(), blank=True, null=True, default=None)
    companies = JSONField(null=True, default=None)

    product = models.CharField(max_length=MAX_LENGTH, null=True)
    source = models.CharField(
        choices=BARRIER_SOURCE, max_length=25, null=True, help_text="chance of success"
    )
    other_source = models.CharField(max_length=MAX_LENGTH, null=True)
    barrier_title = models.CharField(max_length=MAX_LENGTH, null=True)
    problem_description = models.TextField(null=True)
    # next steps will be saved here momentarily during reporting.
    # once the report is ready for submission, this will be added as a new note
    next_steps_summary = models.TextField(null=True)
    eu_exit_related = models.PositiveIntegerField(
        choices=ADV_BOOLEAN,
        null=True
    )

    barrier_type = models.ForeignKey(
        BarrierType,
        null=True,
        default=None,
        related_name="barrier_type",
        on_delete=models.SET_NULL,
    )
    barrier_type_category = models.CharField(
        choices=BARRIER_TYPE_CATEGORIES,
        max_length=25,
        null=True,
        default=None,
        help_text="barrier type category",
    )

    reported_on = models.DateTimeField(db_index=True, auto_now_add=True)

    # Barrier status
    status = models.PositiveIntegerField(
        choices=BARRIER_STATUS, default=0, help_text="status of the barrier instance"
    )
    status_summary = models.TextField(
        null=True, default=None, help_text="status summary if provided by user"
    )
    status_date = models.DateTimeField(
        auto_now_add=True, null=True, help_text="date when status action occurred"
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
        "Stage",
        related_name="report_stages",
        through="BarrierReportStage",
        help_text="Store reporting stages before submitting",
    )

    history = HistoricalRecords()

    def __str__(self):
        if self.barrier_title is None:
            return self.code
        return self.barrier_title

    objects = models.Manager()
    reports = ReportManager()
    barriers = BarrierManager()

    def current_progress(self):
        """ checks current dataset to see how far reporting workflow is done """
        progress_list = []
        for stage in REPORT_CONDITIONS:
            stage_code, status = report_stage_status(self, stage)
            progress_list.append((Stage.objects.get(code=stage_code), status))

        return progress_list

    def submit_report(self, submitted_by=None):
        """ submit a report, convert it into a barrier. Changing status, essentially """
        for validator in [validators.ReportReadyForSubmitValidator()]:
            validator.set_instance(self)
            validator()
        if self.is_resolved:
            barrier_new_status = 4  # Resolved
            status_date = self.isodate_to_tz_datetime(self.resolved_date)
        else:
            barrier_new_status = 2  # Assesment
            status_date = timezone.now()
        self.modified_by = submitted_by
        self.status = barrier_new_status  # If all good, then accept the report for now
        self.reported_on = timezone.now()
        self.status_date = status_date
        self.save()
        return self

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)

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
        super(BarrierInstance, self).save(
            force_insert, force_update, using, update_fields
        )


class BarrierReportStage(BaseModel):
    """ Many to Many between report and workflow stage """

    barrier = models.ForeignKey(
        BarrierInstance, related_name="progress", on_delete=models.PROTECT
    )
    stage = models.ForeignKey(Stage, related_name="progress", on_delete=models.CASCADE)
    status = models.PositiveIntegerField(choices=STAGE_STATUS, null=True)

    history = HistoricalRecords()

    class Meta:
        unique_together = (("barrier", "stage"),)
