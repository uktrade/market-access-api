# Generated by Django 4.2.18 on 2025-02-25 00:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("barriers", "0172_alter_barrier_trading_bloc_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoricalEstimatedResolutionDateRequest",
            fields=[
                (
                    "id",
                    models.IntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                (
                    "estimated_resolution_date",
                    models.DateField(
                        blank=True,
                        help_text="Proposed estimated resolution date",
                        null=True,
                    ),
                ),
                (
                    "reason",
                    models.TextField(
                        blank=True,
                        help_text="Reason for proposed estimated resolution date",
                        null=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("NEEDS_REVIEW", "Needs Review"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                            ("CLOSED", "Closed"),
                        ]
                    ),
                ),
                ("created_on", models.DateTimeField(editable=False, null=True)),
                ("modified_on", models.DateTimeField(null=True)),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
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
                        to="barriers.barrier",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        help_text="User who created the proposed date",
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
                "verbose_name": "historical estimated resolution date request",
                "verbose_name_plural": "historical estimated resolution date requests",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="EstimatedResolutionDateRequest",
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
                    "estimated_resolution_date",
                    models.DateField(
                        blank=True,
                        help_text="Proposed estimated resolution date",
                        null=True,
                    ),
                ),
                (
                    "reason",
                    models.TextField(
                        blank=True,
                        help_text="Reason for proposed estimated resolution date",
                        null=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("NEEDS_REVIEW", "Needs Review"),
                            ("APPROVED", "Approved"),
                            ("REJECTED", "Rejected"),
                            ("CLOSED", "Closed"),
                        ]
                    ),
                ),
                ("created_on", models.DateTimeField(editable=False, null=True)),
                ("modified_on", models.DateTimeField(null=True)),
                (
                    "barrier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="estimated_resolution_date_request",
                        to="barriers.barrier",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="User who created the proposed date",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="estimated_resolution_date_request_user",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "modified_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="estimated_resolution_date_request_modified_by",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
