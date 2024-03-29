# Generated by Django 2.0.5 on 2018-09-24 17:01

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("barriers", "0012_auto_20180924_1654"),
    ]

    operations = [
        migrations.CreateModel(
            name="BarrierCompany",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, db_index=True, null=True),
                ),
                ("modified_on", models.DateTimeField(auto_now=True, null=True)),
                ("company_id", models.UUIDField(help_text="Data hub company UUID")),
                (
                    "company_name",
                    models.CharField(help_text="Data hub company name", max_length=255),
                ),
                (
                    "barrier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="companies",
                        to="barriers.BarrierInstance",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "modified_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HistoricalBarrierCompany",
            fields=[
                (
                    "id",
                    models.IntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(
                        blank=True, db_index=True, editable=False, null=True
                    ),
                ),
                (
                    "modified_on",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                ("company_id", models.UUIDField(help_text="Data hub company UUID")),
                (
                    "company_name",
                    models.CharField(help_text="Data hub company name", max_length=255),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                ("history_date", models.DateTimeField()),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "barrier",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="barriers.BarrierInstance",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "modified_by",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical barrier company",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": "history_date",
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.AlterUniqueTogether(
            name="barriercompany", unique_together={("barrier", "company_id")}
        ),
    ]
