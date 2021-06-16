from uuid import uuid4

from api.barriers.models import Barrier
from django.contrib.auth import get_user_model
from django.db import models
from model_utils.choices import Choices

User = get_user_model()


class ActionPlan(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid4)
    barrier = models.ForeignKey(
        Barrier, on_delete=models.CASCADE, related_name="action_plans"
    )

    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_action_plans",
    )

    current_status = models.TextField(default="", blank=True)


class ActionPlanMilestone(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid4)
    action_plan = models.ForeignKey(
        ActionPlan, related_name="milestones", on_delete=models.CASCADE
    )

    objective = models.TextField()
    completion_date = models.DateField()


ACTION_PLAN_TASK_CHOICES = Choices(
    ("NOT_STARTED", "Not started"),
    ("IN_PROGRESS", "In progress"),
    ("COMPLETED", "Completed"),
)

ACTION_PLAN_TASK_TYPE_CHOICES = Choices(
    ("SCOPING_AND_RESEARCH", "Scoping/Research"),
    ("LOBBYING", "Lobbying"),
    ("UNILATERAL_INTERVENTIONS", "Unilateral interventions"),
    ("BILATERAL_ENGAGEMENT", "Bilateral engagement"),
    ("PLURILATERAL_ENGAGEMENT", "Plurilateral engagement"),
    ("MULTILATERAL_ENGAGEMENT", "Multilateral engagement"),
    ("EVENT", "Event"),
    ("WHITEHALL_FUNDING_STREAMS", "Whitehall funding streams"),
    ("RESOLUTION_NOT_LEAD_BY_DIT", "Resolution not lead by DIT"),
    ("OTHER", "Other"),
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

