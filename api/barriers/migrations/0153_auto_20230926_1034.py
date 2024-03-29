# Generated by Django 3.2.20 on 2023-09-26 10:34

from django.db import migrations, models


def rename_regional_to_overseas(apps, schema_editor):
    BarrierModel = apps.get_model("barriers", "Barrier")
    BarrierModel.objects.filter(priority_level="REGIONAL").update(
        priority_level="OVERSEAS"
    )


def rename_overseas_to_regional(apps, schema_editor):
    BarrierModel = apps.get_model("barriers", "Barrier")
    BarrierModel.objects.filter(priority_level="OVERSEAS").update(
        priority_level="REGIONAL"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("barriers", "0152_remove_historicalbarrier_top_priority_barrier_summary"),
    ]

    operations = [
        migrations.AlterField(
            model_name="barrier",
            name="priority_level",
            field=models.CharField(
                blank=True,
                choices=[
                    ("NONE", ""),
                    ("OVERSEAS", "Overseas Delivery"),
                    ("REGIONAL", "Regional Priority"),
                    ("COUNTRY", "Country Priority"),
                    ("WATCHLIST", "Watch list"),
                ],
                default="NONE",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="historicalbarrier",
            name="priority_level",
            field=models.CharField(
                blank=True,
                choices=[
                    ("NONE", ""),
                    ("OVERSEAS", "Overseas Delivery"),
                    ("REGIONAL", "Regional Priority"),
                    ("COUNTRY", "Country Priority"),
                    ("WATCHLIST", "Watch list"),
                ],
                default="NONE",
                max_length=20,
            ),
        ),
        migrations.RunPython(rename_regional_to_overseas, rename_overseas_to_regional),
    ]
