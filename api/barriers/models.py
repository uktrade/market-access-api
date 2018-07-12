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
    REPORT_STATUS,
)


class CommodityCode(models.Model):

    code = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.name
