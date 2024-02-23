import logging

from rest_framework import serializers

from api.barriers.models import BarrierRequestDownloadApproval

logger = logging.getLogger(__name__)


class BarrierRequestDownloadApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarrierRequestDownloadApproval
        fields = ("id", "user")
