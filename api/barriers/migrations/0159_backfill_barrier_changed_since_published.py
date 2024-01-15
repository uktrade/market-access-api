from django.db import migrations
from api.barriers.migrations.scripts import backfill_barrier_changed_since_published


def backfill_changed_since_published(apps, schema_editor):
    backfill_barrier_changed_since_published.run(
        historical_barrier_model=apps.get_model('barriers', 'HistoricalBarrier'),
        public_barrier_model=apps.get_model('barriers', 'PublicBarrier')
    )


def back(apps, schema_editor):
    """Reverse"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('barriers', '0158_auto_20240110_2208'),
    ]

    operations = [
        migrations.RunPython(backfill_changed_since_published, back),
    ]
