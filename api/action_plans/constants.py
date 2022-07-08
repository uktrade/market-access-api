from django.db import models
from model_utils.choices import Choices

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

ACTION_PLAN_RAG_STATUS_CHOICES = Choices(
    ("ON_TRACK", "On track"),
    ("RISK_OF_DELAY", "Risk of delay"),
    ("DELAYED", "Delayed"),
)


class ActionPlanStakeholderStatus(models.TextChoices):
    FRIEND = ("FRIEND", "Friend")
    NEUTRAL = ("NEUTRAL", "Neutral")
    TARGET = ("TARGET", "Target")
    BLOCKER = ("BLOCKER", "Blocker")
