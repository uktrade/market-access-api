from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .factories import HistoryItemFactory

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class CachedHistoryItem(models.Model):
    barrier = models.ForeignKey(
        "barriers.Barrier",
        related_name="cached_history_items",
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField()
    model = models.CharField(max_length=MAX_LENGTH)
    field = models.CharField(max_length=MAX_LENGTH)
    new_record_content_type = models.ForeignKey(
        ContentType,
        null=True,
        on_delete=models.SET_NULL,
        related_name="new_record_history_items",
    )
    new_record_id = models.PositiveIntegerField(null=True)
    new_record = GenericForeignKey(
        "new_record_content_type",
        "new_record_id",
    )
    old_record_content_type = models.ForeignKey(
        ContentType,
        null=True,
        on_delete=models.SET_NULL,
        related_name="old_record_history_items",
    )
    old_record_id = models.PositiveIntegerField(null=True)
    old_record = GenericForeignKey(
        "old_record_content_type",
        "old_record_id",
    )

    class Meta:
        ordering = ("date",)

    @classmethod
    def create_from_history_item(cls, history_item):
        cls.objects.get_or_create(
            barrier_id=history_item.get_barrier_id(),
            date=history_item.new_record.history_date,
            model=history_item.model,
            field=history_item.field,
            defaults={
                "old_record": history_item.old_record,
                "new_record": history_item.new_record,
            },
        )

    def as_history_item(self):
        return HistoryItemFactory.create(
            field=self.field,
            new_record=self.new_record,
            old_record=self.old_record,
        )
