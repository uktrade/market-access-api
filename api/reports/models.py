from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from api.metadata.constants import (
    ADV_BOOLEAN,
    ESTIMATED_LOSS_RANGE,
    GOVT_RESPONSE,
    PROBLEM_STATUS_TYPES,
    PUBLISH_RESPONSE,
    REPORT_STATUS,
    STAGE_STATUS,
    SUPPORT_TYPE,
)
from api.metadata.models import BarrierType
from api.reports import validators
from api.reports.stage_fields import REPORT_CONDITIONS, stage_status
from api.reports.validators import ReportCompleteValidator


class ReportStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    report = models.ForeignKey(
        "Report", related_name="report_status", on_delete=models.PROTECT
    )
    status = models.PositiveIntegerField(choices=REPORT_STATUS, default=0)
    comments = models.TextField(null=True)
    created_on = models.DateTimeField(db_index=True, auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


class Stage(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid4)
    code = models.CharField(max_length=4, null=False)
    description = models.CharField(max_length=255)
    parent = models.ForeignKey("self", blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.code


class Report(models.Model):

    # id = models.UUIDField(primary_key=True, default=uuid4)
    # 1.1 Status of the problem
    problem_status = models.PositiveIntegerField(
        choices=PROBLEM_STATUS_TYPES, null=True
    )
    is_emergency = models.NullBooleanField()
    # 1.2 Export company affected
    company_id = models.UUIDField(null=True)
    company_name = models.CharField(max_length=255, null=True)
    company_sector = models.UUIDField(null=True)
    company_sector_name = models.CharField(max_length=255, null=True)
    # 1.3 contact
    contact_id = models.UUIDField(null=True)
    # 1.4 About the problem
    product = models.CharField(max_length=255, null=True)
    commodity_codes = models.CharField(max_length=255, null=True)
    export_country = models.UUIDField(null=True)
    problem_description = models.TextField(null=True)
    barrier_title = models.CharField(max_length=255, null=True)
    # 1.5 Impact of the problem
    problem_impact = models.TextField(null=True)
    estimated_loss_range = models.PositiveIntegerField(
        choices=ESTIMATED_LOSS_RANGE, null=True
    )
    other_companies_affected = models.PositiveIntegerField(
        choices=ADV_BOOLEAN, null=True
    )
    other_companies_info = models.TextField(null=True)
    # 1.6 infringements
    has_legal_infringement = models.PositiveIntegerField(choices=ADV_BOOLEAN, null=True)
    wto_infringement = models.NullBooleanField()
    fta_infringement = models.NullBooleanField()
    other_infringement = models.NullBooleanField()
    infringement_summary = models.TextField(null=True)
    # 1.7 Barrier type
    barrier_type = models.ForeignKey(
        BarrierType,
        null=True,
        default=None,
        related_name="report_barrier",
        on_delete=models.SET_NULL,
    )
    # 2.1 Tell us what happens next
    is_resolved = models.NullBooleanField()
    resolved_date = models.DateField(null=True, default=None)
    resolution_summary = models.TextField(null=True)
    support_type = models.PositiveIntegerField(choices=SUPPORT_TYPE, null=True)
    steps_taken = models.TextField(null=True)
    is_politically_sensitive = models.NullBooleanField()
    political_sensitivity_summary = models.TextField(null=True)
    # 2.2 Next steps requested
    govt_response_requested = models.PositiveIntegerField(
        choices=GOVT_RESPONSE, null=True
    )
    is_commercially_sensitive = models.NullBooleanField()
    commercial_sensitivity_summary = models.TextField(null=True)
    can_publish = models.PositiveIntegerField(choices=PUBLISH_RESPONSE, null=True)

    created_on = models.DateTimeField(
        db_index=True, null=True, blank=True, auto_now_add=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    stages = models.ManyToManyField(
        "Stage", related_name="report_stages", through="ReportStage"
    )

    # status = models.ForeignKey(
    #     ReportStatus,
    #     related_name='report_status',
    #     on_delete=models.CASCADE
    # )

    status = models.PositiveIntegerField(choices=REPORT_STATUS, default=0)

    def __str__(self):
        return self.barrier_title

    def complete(self):
        for validator in [validators.ReportCompleteValidator()]:
            validator.set_instance(self)
            validator()
        self.status = 2  # If all good, then accept the report for now
        self.save()

    def current_stage(self):
        progress = []
        for stage in REPORT_CONDITIONS:
            stage_code, status = stage_status(self, stage)
            progress.append((Stage.objects.get(code=stage_code), status))

        return progress


class ReportStage(models.Model):
    report = models.ForeignKey(
        Report, related_name="progress", on_delete=models.PROTECT
    )
    stage = models.ForeignKey(Stage, related_name="progress", on_delete=models.CASCADE)
    status = models.PositiveIntegerField(choices=STAGE_STATUS, null=True)
    created_on = models.DateTimeField(db_index=True, auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = (("report", "stage"),)
