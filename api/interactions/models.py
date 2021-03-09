import re

from api.barriers.mixins import BarrierRelatedMixin
from api.core.models import ArchivableMixin, BaseModel
from api.documents.models import AbstractEntityDocumentModel
from api.metadata.constants import BARRIER_INTERACTION_TYPE

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.urls import reverse

from notifications_python_client.notifications import NotificationsAPIClient
from simple_history.models import HistoricalRecords

MAX_LENGTH = settings.CHAR_FIELD_MAX_LENGTH


class Document(AbstractEntityDocumentModel):
    """ Document item related to interaction """

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
    """ Manage barrier interactions within the model, with archived not False """

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
    email_used = models.EmailField
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )


def _handle_tagged_users(note_text, barrier, created_by):
    # Prepare values used in mentions
    user_regex = re.compile("\@[a-zA-Z.]+\@[a-zA-Z.]+\.gov\.uk")  # noqa W605
    emails = (i[1:] for i in user_regex.finditer(note_text))
    barrier_id = str(barrier.id)
    barrier_name = str(barrier.title)
    mentioned_by = "anonymous"
    if created_by:
        mentioned_by = f"{created_by.first_name} {created_by.last_name}"

    # prepare structures used to record and send mentions
    user_obj = get_user_model()
    users = {u.email: u for u in user_obj.objects.filter(email__in=emails)}
    mentions = []
    client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
    for email in emails:
        first_name = email.split(".")[0]
        client.send_email_notification(
            email_address=email,
            template_id=settings.NOTIFY_BARRIER_NOTIFCATION_ID,
            personalisation={
                "first_name": first_name,
                "mentioned_by": mentioned_by,
                "barrier_number": barrier_id,
                "barrier_name": barrier_name,
            },
        )

        mentions.append(
            Mention(
                created_by=created_by,
                modified_by=created_by,
                barrier=barrier,
                email_used=email,
                recipient=users[email],
            )
        )

    Mention.objects.bulk_create(mentions)


class Interaction(ArchivableMixin, BarrierRelatedMixin, BaseModel):
    """ Interaction records for each Barrier """

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
        _handle_tagged_users(self.text, self.barrier, self.created_by)

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        _handle_tagged_users(self.text, self.public_barrier, self.created_by)

    @property
    def barrier(self):
        return self.public_barrier.barrier

    @property
    def created_user(self):
        return self._cleansed_username(self.created_by)

    @property
    def modified_user(self):
        return self._cleansed_username(self.modified_by)
