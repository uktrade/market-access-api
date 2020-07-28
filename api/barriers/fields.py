from rest_framework import serializers

from api.barriers.helpers import get_or_create_public_barrier
from api.metadata.constants import PublicBarrierStatus


class PublicEligibilityField(serializers.BooleanField):

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        public_barrier, created = get_or_create_public_barrier(self.parent.instance)

        if value is True and public_barrier._public_view_status in (
            PublicBarrierStatus.INELIGIBLE,
            PublicBarrierStatus.UNKNOWN,
        ):
            public_barrier.public_view_status = PublicBarrierStatus.ELIGIBLE
            public_barrier.save()
        elif value is False:
            public_barrier.public_view_status = PublicBarrierStatus.INELIGIBLE
            public_barrier.save()

        return value
