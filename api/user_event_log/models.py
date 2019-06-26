from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from api.user_event_log.constants import USER_EVENT_TYPES


class UserEvent(models.Model):
    """
    User event.

    Used to keep a record of specific events that have occurred while the user was using the
    system (e.g. the user downloaded csv data from find barriers).

    Not intended as a replacement for logging, but for cases where we need to record data in a
    more structured fashion and retain it for a longer period of time.
    """

    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    type = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH, choices=USER_EVENT_TYPES)
    api_url_path = models.CharField(verbose_name='API URL path', max_length=5000, db_index=True)
    data = JSONField(null=True, encoder=DjangoJSONEncoder)

    def __str__(self):
        """Human-friendly string representation."""
        return f'{self.timestamp} – {self.adviser} – {self.get_type_display()}'

    class Meta:
        indexes = [
            models.Index(fields=['api_url_path', 'timestamp']),
        ]
        ordering = ('-timestamp', '-pk')
