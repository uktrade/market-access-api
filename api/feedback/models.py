from django.contrib.postgres.fields import ArrayField
from django.db import models

from api.metadata.constants import FEEDBACK_FORM_SATISFACTION_ANSWERS


class Feedback(models.Model):
    """
    Object model to store user-feedback
    """

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