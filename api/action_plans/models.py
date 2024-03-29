from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Q
from django.db.models.signals import post_save
from django.utils import timezone
from simple_history.models import HistoricalRecords

from api.barriers.models import Barrier
from api.history.v2.service import get_model_history

from .constants import (
    ACTION_PLAN_HAS_RISKS,
    ACTION_PLAN_RAG_STATUS_CHOICES,
    ACTION_PLAN_RISK_LEVEL_CHOICES,
    ACTION_PLAN_TASK_CHOICES,
    ACTION_PLAN_TASK_TYPE_CHOICES,
    ActionPlanStakeholderStatus,
)

User = get_user_model()


class ActionPlanManager(models.Manager):
    def get_active_action_plans(self):
        """
        Return action plans that have at least one non null fields

        """
        return (
            self.get_queryset()
            .annotate(num_milestones=Count("milestones"))
            .annotate(num_stakeholders=Count("stakeholders"))
            .filter(
                Q(current_status__gt="")
                | Q(status__gt="")
                | Q(strategic_context__gt="")
                | Q(has_risks__gt="")
                | Q(potential_unwanted_outcomes__gt="")
                | Q(risk_level__isnull=False)
                | Q(potential_risks__gt="")
                | Q(risk_mitigation_measures__gt="")
                | Q(num_milestones__gt=0)
                | Q(num_stakeholders__gt=0)
            )
        )


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

    # Risks and Mitigations values
    has_risks = models.CharField(
        max_length=100, null=True, blank=True, choices=ACTION_PLAN_HAS_RISKS
    )
    potential_unwanted_outcomes = models.TextField(blank=True, null=True)
    potential_risks = models.TextField(blank=True, null=True)
    risk_level = models.CharField(
        choices=ACTION_PLAN_RISK_LEVEL_CHOICES, max_length=20, null=True
    )
    risk_mitigation_measures = models.TextField(blank=True, null=True)

    history = HistoricalRecords()
    objects = ActionPlanManager()

    def save(self, *args, **kwargs):
        if self.strategic_context:
            self.strategic_context_last_updated = timezone.now()
        if self.current_status:
            self.current_status_last_updated = timezone.now()

        super().save(*args, **kwargs)

    @classmethod
    def get_history(cls, barrier_id):
        qs = cls.history.filter(barrier__id=barrier_id)
        fields = (
            "strategic_context",
            "owner",
            ["owner__id", "owner__first_name", "owner__last_name"],
        )
        return get_model_history(
            qs,
            model="action_plan",
            fields=fields,
            track_first_item=True,
        )


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

    @classmethod
    def get_history(cls, barrier_id):
        qs = cls.history.filter(action_plan__barrier_id=barrier_id)
        fields = ("objective",)
        return get_model_history(
            qs,
            model="action_plan_milestone",
            fields=fields,
            track_first_item=True,
        )


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
    reason_for_completion_date_change = models.TextField(default="", blank=True)

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

    assigned_stakeholders = models.ManyToManyField(
        "Stakeholder",
        blank=True,
    )
    outcome = models.TextField(default="", blank=True)
    progress = models.TextField(default="", blank=True)

    history = HistoricalRecords()

    @classmethod
    def get_history(cls, barrier_id):
        qs = cls.history.filter(milestone__action_plan__barrier_id=barrier_id)
        fields = (
            ["assigned_to__first_name", "assigned_to__last_name"],
            "progress",
            "completion_date",
            "action_type",
            "action_text",
            "action_type_category",
        )
        return get_model_history(
            qs,
            model="action_plan_task",
            fields=fields,
            track_first_item=True,
        )

    class Meta:
        ordering = ("start_date", "completion_date")


class Stakeholder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    action_plan = models.ForeignKey(
        to=ActionPlan, related_name="stakeholders", on_delete=models.CASCADE
    )
    name = models.TextField(default="", blank=True)
    status = models.CharField(
        max_length=7,
        choices=ActionPlanStakeholderStatus.choices,
        default=ActionPlanStakeholderStatus.NEUTRAL,
    )
    organisation = models.TextField(default="", blank=True)
    job_title = models.TextField(default="", blank=True)
    is_organisation = models.BooleanField(default=False)

    class Meta:
        ordering = ("name",)
