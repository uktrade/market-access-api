import uuid
from logging import getLogger

from django.contrib.auth import get_user_model
from django.db import models

from api.core.models import ArchivableMixin, BaseModel

logger = getLogger(__name__)


User = get_user_model()


class BarrierReport(ArchivableMixin, BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="barrier_reports",
        null=True,
        help_text="User who created the barrier report",
    )
