import uuid
from logging import getLogger

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from api.barrier_reports.exceptions import BarrierReportStatusUpdateError
from api.core.models import ArchivableMixin, BaseModel

logger = getLogger(__name__)

User = get_user_model()


class BarrierReportStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETE = 'COMPLETE', 'Complete'


class BarrierReport(ArchivableMixin, BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=128, help_text="User defined report name", null=True)
    status = models.CharField(choices=BarrierReportStatus.choices, default=BarrierReportStatus.PENDING)
    user = models.ForeignKey(User, related_name='barrier_reports', on_delete=models.SET_NULL, null=True)
    filename = models.CharField(max_length=settings.CHAR_FIELD_MAX_LENGTH)

    def processing(self):
        if self.status != BarrierReportStatus.PENDING:
            raise BarrierReportStatusUpdateError("Can only process a pending Barrier Report")
        self.status = BarrierReportStatus.PROCESSING
        self.save()

    def complete(self):
        if self.status != BarrierReportStatus.PROCESSING:
            raise BarrierReportStatusUpdateError("Can only complete a processing Barrier Report")
        self.status = BarrierReportStatus.COMPLETE
        self.save()

    def presigned_url(self):
        """
        if s3 not exists:
        """
        if not self.from_s3():
            raise Exception