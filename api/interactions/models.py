import re
import urllib.parse
from typing import Dict, List, Union

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.urls import reverse
from notifications_python_client.notifications import NotificationsAPIClient
from simple_history.models import HistoricalRecords

from api.barriers.mixins import BarrierRelatedMixin
from api.collaboration.models import TeamMember
from api.core.models import ArchivableMixin, BaseModel
from api.documents.models import AbstractEntityDocumentModel
from api.history.v2 import service as history_service
from api.metadata.constants import BARRIER_INTERACTION_TYPE
from api.user import helpers, staff_sso

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Document(AbstractEntityDocumentModel):
    """Document item related to interaction"""

    size = models.IntegerField(null=True)
    mime_type = models.CharField(max_length=MAX_LENGTH, blank=True)
    detached = models.BooleanField(default=False)

    history = HistoricalRecords()

    @property
    def url(self):
        """Returns URL to download endpoint."""
        return reverse(
            "barrier-document-item-download", kwargs={"entity_document_pk": self.pk}
        )


class InteractionManager(models.Manager):
    """Manage barrier interactions within the model, with archived not False"""

    def get_queryset(self):
        return super(InteractionManager, self).get_queryset().filter(Q(archived=False))


class InteractionHistoricalModel(models.Model):
    """
    Abstract model for history models tracking document changes.
    """

    documents_cache = ArrayField(
        models.JSONField(),
        blank=True,
        default=list,
    )

    def get_changed_fields(self, old_history):
        changed_fields = self.diff_against(old_history).changed_fields

        if "archived" in changed_fields:
            if self.documents_cache:
                return ["text", "documents"]
            return ["text"]

        if "documents" in changed_fields:
            changed_fields.remove("documents")

        new_document_ids = [doc["id"] for doc in self.documents_cache or []]
        old_document_ids = [doc["id"] for doc in old_history.documents_cache or []]
        if set(new_document_ids) != set(old_document_ids):
            changed_fields.append("documents")

        return changed_fields

    def update_documents(self):
        self.documents_cache = [
            {
                "id": str(document["id"]),
                "name": document["original_filename"],
            }
            for document in self.instance.documents.values("id", "original_filename")
        ]

    def save(self, *args, **kwargs):
        self.update_documents()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class Mention(BaseModel):
    barrier = models.ForeignKey(
        "barriers.Barrier",
        related_name="mention",
        on_delete=models.CASCADE,
    )
    email_used = models.EmailField()
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    read_by_recipient = models.BooleanField(default=False)
    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey("content_type", "object_id")
    text = models.TextField()

    class Meta:
        ordering = [
            "-created_on",
        ]

    def get_related_message(self):
        return self.text


class ExcludeFromNotification(BaseModel):
    excluded_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        related_name="excluded_notification",
    )
    exclude_email = models.EmailField()


class Interaction(ArchivableMixin, BarrierRelatedMixin, BaseModel):
    """Interaction records for each Barrier"""

    barrier = models.ForeignKey(
        "barriers.Barrier",
        related_name="interactions_documents",
        on_delete=models.CASCADE,
    )
    kind = models.CharField(choices=BARRIER_INTERACTION_TYPE, max_length=25)
    text = models.TextField(blank=True)
    pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    documents = models.ManyToManyField(
        Document, related_name="documents", help_text="Interaction documents"
    )

    history = HistoricalRecords(bases=[InteractionHistoricalModel])

    objects = InteractionManager()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        _handle_mention_notification(self, self.barrier, self.created_by)

    def get_note_url_path(self):
        """
        Get the frontend url path used in emails and other notifications
        """
        return f"/barriers/{self.barrier.id}/"

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)


class PublicBarrierNote(ArchivableMixin, BarrierRelatedMixin, BaseModel):
    public_barrier = models.ForeignKey(
        "barriers.PublicBarrier",
        related_name="notes",
        on_delete=models.CASCADE,
    )
    text = models.TextField()

    history = HistoricalRecords()

    def save(self, *args, trigger_mentions=True, **kwargs):
        super().save(*args, **kwargs)
        if trigger_mentions:
            _handle_mention_notification(
                self, self.public_barrier.barrier, self.created_by
            )

    def get_note_url_path(self):
        """
        Get the frontend url path used in emails and other notifications
        """
        return f"/barriers/{self.barrier.id}/public/"

    @property
    def barrier(self):
        return self.public_barrier.barrier

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)

    @classmethod
    def get_history(cls, barrier_id):

        qs = cls.history.filter(public_barrier__barrier_id=barrier_id).order_by("id")

        fields = (
            "text",
            "archived",
        )
        return history_service.get_model_history(
            qs,
            model="public_barrier_note",
            fields=fields,
            track_first_item=True,
        )


# Manual made types from readability
user_type = settings.AUTH_USER_MODEL
user_type = Dict[str, settings.AUTH_USER_MODEL]
note_union = Union[Interaction, PublicBarrierNote]


def _get_user_object(emails: List[str]) -> List[user_type]:
    # This function exists to make unit tests easier to write
    output: List[settings.AUTH_USER_MODEL] = []
    for email in emails:
        sso_json = staff_sso.sso.get_user_details_by_email(email)
        user = helpers.get_django_user_by_sso_user_id(sso_json["user_id"])
        output.append(user)

    return output


def _get_mentioned_users(note_text: str) -> user_type:
    regex = r"@\S*?@\S*?gov\.uk"
    matches = re.finditer(regex, note_text, re.MULTILINE)
    emails: List[str] = sorted(
        {m.group()[1:].lower() for m in matches}
    )  # dedupe emails, strip leading '@'

    users: List[user_type] = _get_user_object(emails)
    output: user_type = dict(zip(emails, users))

    return output


def _remove_excluded(emails: List[str]) -> List[str]:
    exclude_emails: List[str] = [
        i.exclude_email
        for i in ExcludeFromNotification.objects.annotate(
            lowered_exclude_email=Lower("exclude_email")
        ).filter(lowered_exclude_email__in=emails)
    ]
    return [e for e in emails if e not in exclude_emails]


def _handle_mention_notification(
    note: note_union,
    barrier,
    created_by,
) -> None:
    # Prepare values used in mentions
    note_text = note.text
    note_url_path = note.get_note_url_path()
    users: user_type = _get_mentioned_users(str(note_text))
    # record mentions
    mentions: List[Mention] = [
        Mention(
            created_by=created_by,
            modified_by=created_by,
            barrier=barrier,
            email_used=email,
            recipient=user,
            text=note_text,
            content_object=note,
        )
        for email, user in users.items()
    ]
    Mention.objects.bulk_create(mentions)

    for user in users.values():
        TeamMember.objects.get_or_create(
            created_by=created_by,
            modified_by=created_by,
            barrier=barrier,
            user=user,
            role=TeamMember.CONTRIBUTOR,
        )

    # prepare values used in notifications
    barrier_code: str = str(barrier.code)
    barrier_name: str = str(barrier.title)
    barrier_url: str = urllib.parse.urljoin(settings.FRONTEND_DOMAIN, note_url_path)
    mentioned_by: str = f"{created_by.first_name} {created_by.last_name}"

    # Send notification
    notification_emails: List[str] = _remove_excluded(list(users.keys()))
    client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
    for email in notification_emails:
        first_name: str = email.split(".")[0]
        first_name = first_name.capitalize()
        client.send_email_notification(
            email_address=email,
            template_id=settings.NOTIFY_BARRIER_NOTIFCATION_ID,
            personalisation={
                "first_name": first_name,
                "mentioned_by": mentioned_by,
                "barrier_number": barrier_code,
                "barrier_name": barrier_name,
                "barrier_url": barrier_url,
            },
        )
