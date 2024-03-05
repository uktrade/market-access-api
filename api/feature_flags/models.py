from django.conf import settings
from django.db import models

from api.core.models import BaseModel


class FlagStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class Flag(BaseModel):
    name = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=128, choices=FlagStatus.choices)


class UserFlag(BaseModel):
    flag = models.ForeignKey(Flag, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="flags"
    )

    class Meta:
        unique_together = ("flag", "user")
