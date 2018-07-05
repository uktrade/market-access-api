from django.db import models

from api.metadata.constants import BARRIER_TYPE_CATEGORIES


class BarrierType(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    category = models.CharField(
        max_length=20,
        choices=BARRIER_TYPE_CATEGORIES,
    )

    def __str__(self):
        return self.title
