from django.db import models

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from api.metadata.constants import (
    PROBLEM_STATUS_TYPES,
    ESTIMATED_LOSS_RANGE,
    STAGE_STATUS,
    ADV_BOOLEAN,
    GOVT_RESPONSE,
    PUBLISH_RESPONSE,
    REPORT_STATUS
)


class Stage(models.Model):
    code = models.CharField(max_length=4, null=False)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.code


class Report(models.Model):

    problem_status = models.PositiveIntegerField(
        choices=PROBLEM_STATUS_TYPES,
        null=True
    )
    is_emergency = models.BooleanField(
        default=False
    )
    company_id = models.UUIDField(
        null=True,
        blank=True
    )
    company_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    contact_id = models.UUIDField(
        null=True,
        blank=True
    )
    product = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    commodity_codes = ArrayField(
        models.CharField(
            max_length=10,
            blank=True,
            null=True,
            default=None
        ),
        null=True
    )
    export_country = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    problem_description = models.TextField(
        null=True
    )
    problem_impact = models.TextField(
        null=True
    )
    estimated_loss_range = models.PositiveIntegerField(
        choices=ESTIMATED_LOSS_RANGE,
        null=True
    )
    other_companies_affected = models.PositiveIntegerField(
        choices=ADV_BOOLEAN,
        null=True
    )
    govt_response_requester = models.PositiveIntegerField(
        choices=GOVT_RESPONSE,
        null=True
    )
    is_confidential = models.NullBooleanField()
    sensitivity_summary = models.TextField(
        null=True
    )
    can_publish = models.PositiveIntegerField(
        choices=PUBLISH_RESPONSE,
        null=True
    )
    name = models.CharField(
        max_length=255,
        null=True
    )
    summary = models.TextField(
        null=True
    )
    stages = models.ManyToManyField(
        Stage,
        related_name="report_stages",
        through="ReportStage"
    )

    status = models.PositiveIntegerField(
        choices=REPORT_STATUS,
        default=0
    )
    status_comments = models.TextField(
        null=True
    )
    created_on = models.DateTimeField(
        db_index=True,
        null=True,
        blank=True,
        auto_now_add=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name


class ReportStage(models.Model):
    report = models.ForeignKey(
        'Report',
        on_delete=models.PROTECT
    )
    stage = models.ForeignKey(
        'Stage',
        on_delete=models.PROTECT
    )
    status = models.PositiveIntegerField(
        choices=STAGE_STATUS,
        null=True
    )
    created_on = models.DateTimeField(
        db_index=True,
        auto_now_add=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = (('report', 'stage'),)
