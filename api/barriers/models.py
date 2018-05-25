# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models

from api.metadata.constants import STATUS_TYPES


class Barrier(models.Model):

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.PositiveIntegerField(choices=STATUS_TYPES, null=True)
    is_emergency = models.BooleanField(default=False)
    company_id = models.UUIDField(null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    export_country = models.CharField(max_length=255, null=True, blank=True)
    # stage?
    # resolution?
    # Need to maintain other users who contribute to this barrier?
    created_on = models.DateTimeField(db_index=True, null=True,
                                      blank=True, auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                   blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.title
