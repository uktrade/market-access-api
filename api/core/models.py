# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import datetime
from django.conf import settings
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Common fields for most of the models we use."""

    created_on = models.DateTimeField(db_index=True, null=True, blank=True, auto_now_add=True)
    modified_on = models.DateTimeField(null=True, blank=True, auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,   
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    class Meta:
        abstract = True

    def isodate_to_tz_datetime(self, isodate):
        """
        Convert an ISO date string 2011-01-01 into a timezone aware datetime that
        has the current timezone.
        """
        date = datetime.strptime(isodate.strftime("%Y-%m-%d"), "%Y-%m-%d")
        current_timezone = timezone.get_current_timezone()
        return current_timezone.localize(date, is_dst=None)


class ArchivableModel(models.Model):
    """Handle model archivation."""

    archived = models.BooleanField(default=False)
    archived_on = models.DateTimeField(blank=True, null=True)
    archived_reason = models.TextField(blank=True, null=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        abstract = True

    def archive(self, user, reason=None):
        """Archive the model instance."""
        self.archived = True
        self.archived_by = user
        self.archived_reason = reason
        self.archived_on = timezone.now()
        self.save()

    def unarchive(self):
        """Unarchive the model instance."""
        self.archived = False
        self.archived_reason = ''
        self.archived_by = None
        self.archived_on = None
        self.save()
