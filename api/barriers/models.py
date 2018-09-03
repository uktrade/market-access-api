from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from api.metadata.constants import (
    ADV_BOOLEAN,
    BARRIER_CHANCE_OF_SUCCESS,
    BARRIER_INTERACTION_TYPE,
    BARRIER_STATUS,
    BARRIER_SOURCE,
    CONTRIBUTOR_TYPE,
    ESTIMATED_LOSS_RANGE,
    GOVT_RESPONSE,
    PROBLEM_STATUS_TYPES,
    STAGE_STATUS,
)
from api.metadata.models import BarrierType
from api.barriers import validators
from api.barriers.report_stages import REPORT_CONDITIONS, report_stage_status


class BarrierStatus(models.Model):
    """ Record each status entry for a Barrier """
    barrier = models.ForeignKey(
        "BarrierInstance",
        related_name="statuses",
        on_delete=models.PROTECT,
        help_text="barrier instance"
    )
    status = models.PositiveIntegerField(
        choices=BARRIER_STATUS,
        help_text="status of the barrier instance"
    )
    summary = models.TextField(
        null=True,
        help_text="status summary if provided by user"
    )
    status_date = models.DateTimeField(
        help_text="date when status action occurred"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="specifies if this barrier status is current or historical"
    )
    created_on = models.DateTimeField(db_index=True, auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )


class BarrierInteraction(models.Model):
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
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL
    )


class Stage(models.Model):
    code = models.CharField(max_length=4, null=False)
    description = models.CharField(max_length=255)
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.code


class BarrierInstance(models.Model):
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
    other_source = models.CharField(max_length=255, null=True)
    barrier_title = models.CharField(max_length=255, null=True)
    problem_description = models.TextField(null=True)

    barrier_type = models.ForeignKey(
        BarrierType,
        null=True,
        default=None,
        related_name="barrier_type",
        on_delete=models.SET_NULL,
    )

    commodity_codes = models.CharField(max_length=255, null=True)
    problem_impact = models.TextField(null=True)

    summary = models.TextField(
        help_text="summary of barrier"
    )
    chance_of_success = models.CharField(
        choices=BARRIER_CHANCE_OF_SUCCESS,
        max_length=25,
        null=True,
        help_text="chance of success"
    )
    chance_of_success_summary = models.TextField(
        null=True,
        help_text="Give an explanation of your choice"
    )
    estimated_loss_range = models.PositiveIntegerField(
        choices=ESTIMATED_LOSS_RANGE,
        null=True,
        default=None,
        help_text="Estimated financial value of sales lost over a five year period"
    )
    impact_summary = models.TextField(
        null=True,
        help_text="Impact the problem expected to have on the company if it is not resolved"
    )
    other_companies_affected = models.PositiveIntegerField(
        choices=ADV_BOOLEAN,
        null=True,
        default=None,
        help_text="Are there other companies affected?"
    )
    has_legal_infringement = models.PositiveIntegerField(
        choices=ADV_BOOLEAN,
        null=True,
        default=None,
        help_text="Legal obligations infringed"
    )
    wto_infringement = models.NullBooleanField(
        help_text="Legal obligations infringed"
    )
    fta_infringement = models.NullBooleanField(
        help_text="Legal obligations infringed"
    )
    other_infringement = models.NullBooleanField(
        help_text="Legal obligations infringed"
    )
    infringement_summary = models.TextField(
        null=True,
        default=None,
        help_text="Summary of infringments"
    )
    reported_on = models.DateTimeField(db_index=True, auto_now_add=True)
    created_on = models.DateTimeField(db_index=True, auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

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

    stages = models.ManyToManyField(
        "Stage", 
        related_name="report_stages", 
        through="BarrierReportStage",
        help_text="Store reporting stages before submitting"
    )

    def __str__(self):
        return self.id

    def current_progress(self):
        progress_list = []
        for stage in REPORT_CONDITIONS:
            stage_code, status = report_stage_status(self, stage)
            progress_list.append((Stage.objects.get(code=stage_code), status))

        return progress_list

    def submit_report(self):
        for validator in [validators.ReportReadyForSubmitValidator()]:
            validator.set_instance(self)
            validator()
        if self.is_resolved:
            barrier_new_status = 4 # Resolved
        else:
            barrier_new_status = 2 # Assesment
        self.status = barrier_new_status  # If all good, then accept the report for now
        self.status_date = timezone.now()
        self.save()

    def _new_status(self, new_status, summary, resolved_date, user):
        try:
            barrier_status = BarrierStatus.objects.get(barrier=self, status=new_status)
            barrier_status.status_date = resolved_date
            barrier_status.summary = summary
            barrier_status.is_active = True
            barrier_status.save()
        except BarrierStatus.DoesNotExist:
            BarrierStatus(
                barrier=self,
                status=new_status,
                summary=summary,
                status_date=resolved_date
            ).save()
            barrier_status = BarrierStatus.objects.get(barrier=self, status=new_status)

        if settings.DEBUG is False:
            barrier_status.created_by = user
            barrier_status.save()

    def resolve(self, summary, resolved_date, user):
        resolved_status = 4 # Resolved
        self._new_status(resolved_status, summary, resolved_date, user)

    def hibernate(self, summary, user):
        hibernate_status = 5 # Hibernated
        self._new_status(hibernate_status, summary, timezone.now(), user)


class BarrierReportStage(models.Model):
    barrier = models.ForeignKey(
        BarrierInstance, related_name="progress", on_delete=models.PROTECT
    )
    stage = models.ForeignKey(Stage, related_name="progress", on_delete=models.CASCADE)
    status = models.PositiveIntegerField(choices=STAGE_STATUS, null=True)
    created_on = models.DateTimeField(db_index=True, auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = (("barrier", "stage"),)


# class BarrierSector(models.Model):
#     """ Sectors for each Barrier """
#     barrier = models.ForeignKey(
#         BarrierInstance,
#         related_name="sectors",
#         on_delete=models.PROTECT
#     )
#     sector_id = models.UUIDField(null=False)
#     created_on = models.DateTimeField(auto_now_add=True)
#     created_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         null=True,
#         on_delete=models.SET_NULL
#     )


class BarrierContributor(models.Model):
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
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL
    )
