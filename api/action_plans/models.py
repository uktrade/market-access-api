from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from simple_history.models import HistoricalRecords

from api.barriers.models import Barrier

from .constants import (
    ACTION_PLAN_RAG_STATUS_CHOICES,
    ACTION_PLAN_TASK_CHOICES,
    ACTION_PLAN_TASK_TYPE_CHOICES,
)

User = get_user_model()


class ActionPlan(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid4)
    barrier = models.OneToOneField(
        Barrier, on_delete=models.CASCADE, related_name="action_plan"
    )

    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_action_plans",
    )

    current_status = models.TextField(default="", blank=True)
    current_status_last_updated = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=100, null=True, blank=True, choices=ACTION_PLAN_RAG_STATUS_CHOICES
    )
    strategic_context = models.TextField(default="", blank=True)
    strategic_context_last_updated = models.DateTimeField(null=True, blank=True)

    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if self.strategic_context:
            self.strategic_context_last_updated = timezone.now()
        if self.current_status:
            self.current_status_last_updated = timezone.now()

        super().save(*args, **kwargs)


def create_action_plan_on_barrier_post_save(sender, instance: Barrier, **kwargs):
    """
    Create an ActionPlan model whenever a Barrier is created.
    At this moment in time Barriers are created via the save method of the model,
    so a signal should be safe to use
    """
    try:
        instance.action_plan
    except Barrier.action_plan.RelatedObjectDoesNotExist:
        ActionPlan.objects.get_or_create(barrier=instance)


post_save.connect(create_action_plan_on_barrier_post_save, sender=Barrier)


class ActionPlanMilestone(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid4)
    action_plan = models.ForeignKey(
        ActionPlan, related_name="milestones", on_delete=models.CASCADE
    )

    objective = models.TextField()
    completion_date = models.DateField(null=True, blank=True)

    history = HistoricalRecords()


class ActionPlanTask(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid4)
    milestone = models.ForeignKey(
        ActionPlanMilestone, related_name="tasks", on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=100,
        choices=ACTION_PLAN_TASK_CHOICES,
        default="NOT_STARTED",
        blank=True,
    )
    start_date = models.DateField(blank=True, null=True)
    completion_date = models.DateField(blank=True, null=True)

    action_text = models.TextField()

    action_type = models.CharField(
        max_length=100, choices=ACTION_PLAN_TASK_TYPE_CHOICES
    )
    action_type_category = models.CharField(
        max_length=100, null=True, blank=True, default="Other"
    )

    assigned_to = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )

    stakeholders = models.TextField(default="", blank=True)
    outcome = models.TextField(default="", blank=True)
    progress = models.TextField(default="", blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ("start_date", "completion_date")
