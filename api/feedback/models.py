from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models

from api.metadata.constants import FEEDBACK_FORM_SATISFACTION_ANSWERS

User = get_user_model()


class Feedback(models.Model):
    """
    Object model to store user-feedback
    """

    created = models.DateTimeField(default=datetime.now, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    satisfaction = models.CharField(
        blank=True,
        default=FEEDBACK_FORM_SATISFACTION_ANSWERS.NONE,
        max_length=40,
        choices=FEEDBACK_FORM_SATISFACTION_ANSWERS,
    )

    # Possible contents;
    # "Report a barrier", "Set a progress update", "Export a barrier CSV report",
    # "Create or edit an action plan", "Other", "Don't know"
    attempted_actions = ArrayField(
        models.CharField(max_length=30),
        blank=True,
        default=list,
    )

    feedback_text = models.TextField(default="", blank=True)
