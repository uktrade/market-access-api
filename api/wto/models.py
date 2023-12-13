from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from simple_history.models import HistoricalRecords

from api.interactions.models import Document
from api.history.utils import get_model_history, FieldMapping

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class WTOCommitteeGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=MAX_LENGTH)

    class Meta:
        ordering = ("name",)


class WTOCommittee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    wto_committee_group = models.ForeignKey(
        "WTOCommitteeGroup",
        related_name="committees",
        on_delete=models.PROTECT,
    )
    name = models.CharField(max_length=MAX_LENGTH)

    class Meta:
        ordering = ("name",)


class WTOProfileHistoricalModel(models.Model):
    def get_changed_fields(self, old_history):
        changed_fields = set(self.diff_against(old_history).changed_fields)

        if changed_fields.intersection(
            ("wto_has_been_notified", "wto_should_be_notified")
        ):
            changed_fields.discard("wto_has_been_notified")
            changed_fields.discard("wto_should_be_notified")
            changed_fields.add("wto_notified_status")

        return list(changed_fields)

    class Meta:
        abstract = True


class WTOProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    barrier = models.OneToOneField(
        "barriers.Barrier",
        on_delete=models.CASCADE,
        related_name="wto_profile",
    )
    wto_has_been_notified = models.BooleanField()
    wto_should_be_notified = models.BooleanField(null=True)
    committee_notified = models.ForeignKey(
        "WTOCommittee",
        related_name="committee_notified_wto_profiles",
        null=True,
        on_delete=models.SET_NULL,
    )
    committee_notification_link = models.CharField(
        max_length=2048,
        blank=True,
    )
    committee_notification_document = models.ForeignKey(
        Document,
        related_name="committee_notification_wto_profiles",
        null=True,
        on_delete=models.SET_NULL,
    )
    member_states = ArrayField(
        models.UUIDField(),
        blank=True,
        default=list,
    )
    committee_raised_in = models.ForeignKey(
        "WTOCommittee",
        related_name="committee_raised_in_wto_profiles",
        null=True,
        on_delete=models.SET_NULL,
    )
    meeting_minutes = models.ForeignKey(
        Document,
        related_name="meeting_minutes_wto_profiles",
        null=True,
        on_delete=models.SET_NULL,
    )
    raised_date = models.DateField(null=True)
    case_number = models.CharField(max_length=MAX_LENGTH, blank=True)

    history = HistoricalRecords(bases=[WTOProfileHistoricalModel])

    @classmethod
    def get_history(cls, barrier_id, status_date=None):
        if not status_date:
            qs = cls.history.filter(barrier__id=barrier_id)
        else:
            qs = cls.history.filter(barrier__id=barrier_id, start_date=status_date)

        fields = (
            "case_number",
            "committee_notified",
            "committee_notification_link",
            "committee_notification_document",
            "meeting_minutes",
            "member_states",
            "committee_raised_in",
            "raised_date",
            "wto_notified_status",
        )
        return get_model_history(
            qs,
            model="wto_profile",
            fields=fields,
            track_first_item=True,
        )
