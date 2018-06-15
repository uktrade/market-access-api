# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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


class CommodityCode(models.Model):

    code = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.name


class ReportStage(models.Model):
    code = models.CharField(max_length=4, null=False)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.code


class Barrier(models.Model):

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
    barrier_name = models.CharField(
        max_length=255,
        null=True
    )
    barrier_summary = models.TextField(
        null=True
    )
    report_stages = models.ManyToManyField(
        ReportStage,
        related_name="report_stages",
        through="BarrierReportStage"
    )

    status = models.PositiveIntegerField(
        choices=REPORT_STATUS,
        default=0
    )
    # Need to maintain other users who contribute to this barrier?
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
        return self.barrier_name


class BarrierReportStage(models.Model):
    barrier = models.ForeignKey(
        'Barrier',
        on_delete=models.PROTECT
    )
    stage = models.ForeignKey(
        'ReportStage',
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
        unique_together = (('barrier', 'stage', 'status'),)


class BarrierCommodityCode(models.Model):
    barrier = models.ForeignKey(
        'Barrier',
        on_delete=models.PROTECT
    )
    commodity_code = models.ForeignKey(
        'CommodityCode',
        on_delete=models.PROTECT
    )
    is_active = models.BooleanField(
        default=False
    )

    class Meta:
        unique_together = (('barrier', 'commodity_code'),)
