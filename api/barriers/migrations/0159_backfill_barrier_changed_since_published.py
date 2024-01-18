from logging import getLogger

from django.db import migrations


logger = getLogger(__name__)


def run(historical_barrier_model, public_barrier_model, dry_run: bool = False):
    public_barriers = public_barrier_model.objects.filter(
        changed_since_published=False
    ).values_list("barrier__id", "last_published_on")

    logger.info(f"Public Barrier Count: {public_barriers.count()}")
    barriers_to_update = []

    for barrier in public_barriers:
        if barrier[1] is not None:
            fields = ["categories_cache", "title", "summary", "country", "sectors", "status"]
            last_history_before_published = historical_barrier_model.objects.filter(
                id=barrier[0], history_date__lte=barrier[1]
            ).order_by('-history_date')[:1].values_list(*fields)

            barrier_history = (
                list(historical_barrier_model.objects.filter(id=barrier[0], history_date__gt=barrier[1]).values_list(*fields))
                + list(last_history_before_published)
            )

            logger.info(
                f"Public Barrier {barrier[0]} History Count: {len(barrier_history)}"
            )
            changed = False
            for i, historical_record in enumerate(barrier_history):
                if i == len(barrier_history) - 1:
                    break

                if any(
                        [
                            historical_record[0] != barrier_history[i + 1][0],
                            historical_record[1] != barrier_history[i + 1][1],
                            historical_record[2] != barrier_history[i + 1][2],
                            historical_record[3] != barrier_history[i + 1][3],
                            historical_record[4] != barrier_history[i + 1][4],
                            historical_record[5] != barrier_history[i + 1][5],
                        ]
                ):
                    changed = True
                    break

            if changed:
                logger.info(f"Barrier {barrier[0]} changed")
                barriers_to_update.append(barrier[0])

    logger.info(f'Barriers To Update: {", ".join(str(barrier) for barrier in barriers_to_update)}')
    if not dry_run and barriers_to_update:
        qs = public_barrier_model.objects.filter(barrier__in=barriers_to_update)
        qs.update(changed_since_published=True)


def backfill_changed_since_published(apps, schema_editor):
    run(
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
