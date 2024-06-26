from django.db import migrations
from django.db import transaction

from api.metadata.constants import PublicBarrierStatus
import logging

logger = logging.getLogger(__name__)


def update_set_to_allowed_on(apps, schema_editor):
    PublicBarrier = apps.get_model("barriers", "PublicBarrier")
    HistoricalPublicBarrier = apps.get_model("barriers", "HistoricalPublicBarrier")

    barrier_ids = PublicBarrier.objects.exclude(
        _public_view_status__in=[PublicBarrierStatus.UNKNOWN, PublicBarrierStatus.NOT_ALLOWED]
    ).values_list('barrier_id', flat=True)

    barrier_date_mapping = {}

    for barrier_id in barrier_ids:
        barriers = list(HistoricalPublicBarrier.objects.filter(barrier_id=barrier_id, _public_view_status__in=[PublicBarrierStatus.ALLOWED, PublicBarrierStatus.NOT_ALLOWED, PublicBarrierStatus.UNKNOWN]).order_by('-history_date'))

        for i, barrier in enumerate(barriers):
            if i == 0 and barrier._public_view_status in [PublicBarrierStatus.NOT_ALLOWED, PublicBarrierStatus.UNKNOWN]:
                break
            if i == len(barriers) - 1 or (barriers[i]._public_view_status == PublicBarrierStatus.ALLOWED and barriers[i+1]._public_view_status in [PublicBarrierStatus.NOT_ALLOWED, PublicBarrierStatus.UNKNOWN]):
                barrier_date_mapping[barrier_id] = barriers[i].history_date
                break

    logger.info(f'Updating set_to_allowed_on for {len(barrier_date_mapping)} barriers')
    with transaction.atomic():
        for barrier_id, history_date in barrier_date_mapping.items():
            PublicBarrier.objects.filter(barrier_id=barrier_id).update(set_to_allowed_on=history_date)

    logger.info(f'Barrier set_to_allowed_on updated for: {list(barrier_date_mapping.keys())}')


class Migration(migrations.Migration):
    dependencies = [
        ("barriers", "0165_historicalpublicbarrier_set_to_allowed_on_and_more"),
    ]

    operations = [
        migrations.RunPython(update_set_to_allowed_on, reverse_code=migrations.RunPython.noop),
    ]
