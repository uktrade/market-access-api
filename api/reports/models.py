from django.db import models

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
    SUPPORT_TYPE
)


class Stage(models.Model):
    code = models.CharField(max_length=4, null=False)
    description = models.CharField(max_length=255)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.code


class Report(models.Model):

    # 1.1
    problem_status = models.PositiveIntegerField(
        choices=PROBLEM_STATUS_TYPES,
        null=True
    )
    is_emergency = models.BooleanField(
        default=False
    )
    # 1.2
    company_id = models.UUIDField(
        null=True,
        blank=True
    )
    company_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    # 1.3
    contact_id = models.UUIDField(
        null=True,
        blank=True
    )
    # 1.4
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
    # 1.5
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
    # 2.0
    name = models.CharField(
        max_length=255,
        null=True
    )
    summary = models.TextField(
        null=True
    )
    # 3.0
    is_resolved = models.NullBooleanField()
    support_type = models.PositiveIntegerField(
        choices=SUPPORT_TYPE,
        null=True
    )

    stages = models.ManyToManyField(
        'Stage',
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

    def current_stage(self):
        if self.is_resolved is not None and self.support_type:
            return (Stage.objects.get(code="3.0"), 3)
        elif self.is_resolved is not None or self.support_type:
            return (Stage.objects.get(code="3.0"), 2)

        if self.name and self.summary:
            return (Stage.objects.get(code="2.0"), 3)
        elif self.name or self.summary:
            return (Stage.objects.get(code="2.0"), 2)

        if self.govt_response_requester and self.is_confidential is not None and self.can_publish is not None:
            return (Stage.objects.get(code="1.5"), 3)    # 1.5
        elif self.govt_response_requester or self.is_confidential is not None or self.can_publish is not None:
            return (Stage.objects.get(code="1.5"), 2)    # 1.5

        if self.product and self.export_country and self.problem_description and self.problem_impact and self.estimated_loss_range and self.other_companies_affected:
            return (Stage.objects.get(code="1.4"), 3)    # 1.4
        elif self.product or self.export_country or self.problem_description or self.problem_impact or self.estimated_loss_range or self.other_companies_affected:
            return (Stage.objects.get(code="1.4"), 2)    # 1.4

        if self.contact_id:
            return (Stage.objects.get(code="1.3"), 3)    # 1.3

        if self.company_id:
            return (Stage.objects.get(code="1.2"), 3)    # 1.2
        if self.problem_status:
            return (Stage.objects.get(code="1.1"), 3)    # 1.1

        return (Stage.objects.get(code="1.1"), 2)


class ReportStage(models.Model):
    report = models.ForeignKey(
        Report,
        related_name='progress',
        on_delete=models.PROTECT
    )
    stage = models.ForeignKey(
        Stage,
        related_name='progress',
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
