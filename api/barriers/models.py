from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.utils import timezone

from simple_history.models import HistoricalRecords

from api.metadata.constants import (
    ADV_BOOLEAN,
    BARRIER_INTERACTION_TYPE,
    BARRIER_STATUS,
    BARRIER_SOURCE,
    CONTRIBUTOR_TYPE,
    PROBLEM_STATUS_TYPES,
    STAGE_STATUS,
)
from api.core.models import BaseModel
from api.metadata.models import BarrierType
from api.barriers import validators
from api.barriers.report_stages import REPORT_CONDITIONS, report_stage_status

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class BarrierInteraction(BaseModel):
    """ Interaction records for each Barrier """
    barrier = models.ForeignKey(
        "BarrierInstance",
        related_name="interactions",
        on_delete=models.PROTECT
    )
    kind = models.CharField(
        choices=BARRIER_INTERACTION_TYPE,
        max_length=25
    )
    text = models.TextField(null=True)
    pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()


class Stage(models.Model):
    """ Reporting workflow stages  """
    code = models.CharField(max_length=4, null=False)
    description = models.CharField(max_length=MAX_LENGTH)
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.code

class DatahubCompany(models.Model):
    """ Local model to store data hub companies for ease  """
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(
        max_length=MAX_LENGTH, blank=True, null=True, help_text='Trading name'
    )

    def __str__(self):
        return self.name


class ReportManager(models.Manager):
    """ Manage reports within the model, with status 0 """
    def get_queryset(self):
        return super(ReportManager, self).get_queryset().filter(Q(status=0))


class BarrierManager(models.Manager):
    """ Manage barriers within the model, with status not 0 """
    def get_queryset(self):
        return super(BarrierManager, self).get_queryset().filter(~Q(status=0))


class BarrierInstance(BaseModel):
    """ Barrier Instance, converted from a completed and accepted Report """
    id = models.UUIDField(primary_key=True, default=uuid4)
    problem_status = models.PositiveIntegerField(
        choices=PROBLEM_STATUS_TYPES, null=True
    )

    is_resolved = models.NullBooleanField()
    resolved_date = models.DateField(null=True, default=None)

    export_country = models.UUIDField(null=True)

    sectors_affected = models.NullBooleanField()
    sectors = ArrayField(
        models.UUIDField(),
        blank=True,
        null=True,
        default=None
    )

    product = models.CharField(max_length=255, null=True)
    source = models.CharField(
        choices=BARRIER_SOURCE,
        max_length=25,
        null=True,
        help_text="chance of success"
    )
    other_source = models.CharField(max_length=MAX_LENGTH, null=True)
    barrier_title = models.CharField(max_length=MAX_LENGTH, null=True)
    problem_description = models.TextField(null=True)

    barrier_type = models.ForeignKey(
        BarrierType,
        null=True,
        default=None,
        related_name="barrier_type",
        on_delete=models.SET_NULL,
    )

    reported_on = models.DateTimeField(db_index=True, auto_now_add=True)

    status = models.PositiveIntegerField(
        choices=BARRIER_STATUS,
        default=0,
        help_text="status of the barrier instance"
    )
    status_summary = models.TextField(
        null=True,
        default=None,
        help_text="status summary if provided by user"
    )
    status_date = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="date when status action occurred"
    )

    has_legal_infringement = models.PositiveIntegerField(
        choices=ADV_BOOLEAN,
        null=True,
        default=None,
        help_text="Legal obligations infringed"
    )
    wto_infringement = models.NullBooleanField(
        default=None,
        help_text="Legal obligations infringed"
    )
    fta_infringement = models.NullBooleanField(
        default=None,
        help_text="Legal obligations infringed"
    )
    other_infringement = models.NullBooleanField(
        default=None,
        help_text="Legal obligations infringed"
    )
    infringement_summary = models.TextField(
        null=True,
        default=None,
        help_text="Summary of infringments"
    )

    political_sensitivities = models.TextField(
        null=True,
        default=None,
        help_text="Political sensitivities to be aware of"
    )

    commercial_sensitivities = models.TextField(
        null=True,
        default=None,
        help_text="Commercial or confidentiality sensitivities to be aware of"
    )

    companies = models.ManyToManyField(
        "DatahubCompany",
        related_name="companies",
        through="BarrierCompany",
        help_text="companies affected by barrier"
    )

    stages = models.ManyToManyField(
        "Stage",
        related_name="report_stages",
        through="BarrierReportStage",
        help_text="Store reporting stages before submitting"
    )

    history = HistoricalRecords()

    def __str__(self):
        return self.barrier_title

    objects = models.Manager()
    reports = ReportManager()
    barriers = BarrierManager()

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

    def submit_report(self):
        """ submit a report, convert it into a barrier. Changing status, essentially """
        for validator in [validators.ReportReadyForSubmitValidator()]:
            validator.set_instance(self)
            validator()
        if self.is_resolved:
            barrier_new_status = 4 # Resolved
            status_date = self.isodate_to_tz_datetime(self.resolved_date)
        else:
            barrier_new_status = 2 # Assesment
            status_date = timezone.now()
        self.status = barrier_new_status  # If all good, then accept the report for now
        self.status_date = status_date
        self.save()

    @property
    def created_by_username(self):
        if self.created_by is not None:
            if self.created_by.username is not None and self.created_by.username.strip() != "":
                if "@" in self.created_by.username:
                    return self.created_by.username.split("@")[0]
                else:
                    return self.created_by.username
            elif self.created_by.email is not None and self.created_by.email.strip() != "":
                return self.created_by.email.split("@")[0]

        return None


class BarrierCompany(BaseModel):
    """ Many to Many between barrier and company """
    barrier = models.ForeignKey(
        BarrierInstance, related_name="companies", on_delete=models.PROTECT
    )
    company_id = models.UUIDField(
        null=False, help_text='Data hub company UUID'
    )
    company_name = models.CharField(
        max_length=MAX_LENGTH, null=False, help_text='Data hub company name'
    )

    history = HistoricalRecords()

    class Meta:
        unique_together = (("barrier", "company_id"),)


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


class BarrierContributor(BaseModel):
    """ Contributors for each Barrier """
    barrier = models.ForeignKey(
        BarrierInstance,
        related_name="contributors",
        on_delete=models.PROTECT
    )
    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="contributor_user",
        null=True,
        on_delete=models.PROTECT
    )
    kind = models.CharField(
        choices=CONTRIBUTOR_TYPE,
        max_length=25
    )
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
