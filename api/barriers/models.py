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
    CONTRIBUTOR_TYPE,
    ESTIMATED_LOSS_RANGE,
    GOVT_RESPONSE,
    PROBLEM_STATUS_TYPES,
    PUBLISH_RESPONSE,
    REPORT_STATUS,
    STAGE_STATUS,
)
from api.metadata.models import BarrierType
from api.reports.models import Report

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
    is_active = models.BooleanField(
        default=True,
        help_text="specifies if this barrier status is current or historical"
    )
    created_on = models.DateTimeField(db_index=True, auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = (("barrier", "status"),)

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


class BarrierInstance(models.Model):
    """ Barrier Instance, converted from a completed and accepted Report """
    id = models.UUIDField(primary_key=True, default=uuid4)
    report = models.ForeignKey(
        Report,
        related_name="barrier_report",
        on_delete=models.PROTECT,
        help_text="originating report"
    )
    barrier_type = models.ForeignKey(
        BarrierType,
        related_name="barrier_barrier_type",
        on_delete=models.PROTECT,
        help_text="market access barrier type"
    )
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
        help_text="Estimated financial value of sales lost over a five year period"
    )
    impact_summary = models.TextField(
        null=True,
        help_text="Impact the problem expected to have on the company if it is not resolved"
    )
    other_companies_affected = models.PositiveIntegerField(
        choices=ADV_BOOLEAN,
        help_text="Are there other companies affected?"
    )
    has_legal_infringement = models.PositiveIntegerField(
        choices=ADV_BOOLEAN,
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
        help_text="Summary of infringments"
    )
    reported_on = models.DateTimeField(db_index=True, auto_now_add=True)
    created_on = models.DateTimeField(db_index=True, auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.report

    def _new_status(self, new_status, user):
        try:
            barrier_status = BarrierStatus.objects.get(barrier=self, status=new_status)
            barrier_status.created_on = timezone.now()
            barrier_status.is_active = True
            barrier_status.save()
        except BarrierStatus.DoesNotExist:
            barrier_status = BarrierStatus(barrier=self, status=new_status).save()

        if settings.DEBUG is False:
            barrier_status.created_by = user
            barrier_status.save()

    def resolve(self, user):
        resolved_status = 4 # Resolved
        self._new_status(resolved_status, user)

    def hibernate(self, user):
        hibernate_status = 5 # Hibernated
        self._new_status(hibernate_status, user)


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
