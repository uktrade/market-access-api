# Generated by Django 4.2.11 on 2024-07-01 11:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("barriers", "0168_refresh_public_barrier_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="barrier",
            name="trading_bloc",
            field=models.CharField(
                blank=True,
                choices=[
                    ("TB00003", "Association of Southeast Asian Nations (ASEAN)"),
                    ("TB00016", "European Union (EU)"),
                    ("TB00017", "Gulf Cooperation Council (GCC)"),
                    ("TB00013", "Eurasian Economic Union (EAEU)"),
                    ("TB00026", "Southern Common Market (Mercosur)"),
                ],
                max_length=7,
            ),
        ),
        migrations.AlterField(
            model_name="historicalbarrier",
            name="trading_bloc",
            field=models.CharField(
                blank=True,
                choices=[
                    ("TB00003", "Association of Southeast Asian Nations (ASEAN)"),
                    ("TB00016", "European Union (EU)"),
                    ("TB00017", "Gulf Cooperation Council (GCC)"),
                    ("TB00013", "Eurasian Economic Union (EAEU)"),
                    ("TB00026", "Southern Common Market (Mercosur)"),
                ],
                max_length=7,
            ),
        ),
    ]
