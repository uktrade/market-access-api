# Generated by Django 4.2.11 on 2024-06-24 11:12

from django.db import migrations, models

from api.barriers.models import Barrier, PublicBarrier


def update_public_barrier_fields(apps, schema_editor):
    barriers = Barrier.objects.all()

    non_editable_public_fields = [
        "status",
        "status_date",
        "reported_on",
        "country",
        "caused_by_trading_bloc",
        "trading_bloc",
        "sectors",
        "main_sector",
        "all_sectors",
    ]

    for barrier in barriers:
        public_barrier = PublicBarrier.objects.get(barrier_id=barrier)

        if public_barrier:
            for field in non_editable_public_fields:
                internal_value = getattr(barrier, field)
                setattr(public_barrier, field, internal_value)
            public_barrier.categories.set(barrier.categories.all())
            public_barrier.save()
            public_barrier.update_changed_since_published()


class Migration(migrations.Migration):

    dependencies = [
        (
            "barriers",
            "0167_remove_historicalpublicbarrier_light_touch_reviews_cache_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            update_public_barrier_fields, reverse_code=migrations.RunPython.noop
        ),
    ]