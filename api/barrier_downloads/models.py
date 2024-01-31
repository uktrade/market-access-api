import uuid
from logging import getLogger

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from api.barrier_downloads.exceptions import BarrierDownloadStatusUpdateError
from api.core.models import ArchivableMixin, BaseModel

logger = getLogger(__name__)

User = get_user_model()


class BarrierDownloadStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETE = "COMPLETE", "Complete"


class BarrierDownload(ArchivableMixin, BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(
        max_length=128, help_text="User defined barrier download name", null=True
    )
    status = models.CharField(
        choices=BarrierDownloadStatus.choices, default=BarrierDownloadStatus.PENDING
    )
    user = models.ForeignKey(
        User, related_name="barrier_downloads", on_delete=models.SET_NULL, null=True
    )
    filename = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)

    def processing(self):
        if self.status != BarrierDownloadStatus.PENDING:
            raise BarrierDownloadStatusUpdateError(
                "Can only process a pending Barrier Download"
            )
        self.status = BarrierDownloadStatus.PROCESSING
        self.save()

    def complete(self):
        if self.status != BarrierDownloadStatus.PROCESSING:
            raise BarrierDownloadStatusUpdateError(
                "Can only complete a processing Barrier Download"
            )
        self.status = BarrierDownloadStatus.COMPLETE
        self.save()
