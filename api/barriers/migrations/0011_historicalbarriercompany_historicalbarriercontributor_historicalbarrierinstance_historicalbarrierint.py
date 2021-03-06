# Generated by Django 2.0.5 on 2018-09-12 20:33

import uuid

import django.contrib.postgres.fields
import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0006_auto_20180903_1349"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("barriers", "0010_auto_20180912_1831"),
    ]

    operations = [
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
                    "company",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="barriers.DatahubCompany",
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
        migrations.CreateModel(
            name="HistoricalBarrierContributor",
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
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("INITIATOR", "Initiator"),
                            ("CONTRIBUTOR", "Contributor"),
                            ("LEAD", "Lead"),
                        ],
                        max_length=25,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
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
                    "contributor",
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
                "verbose_name": "historical barrier contributor",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": "history_date",
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalBarrierInstance",
            fields=[
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
                ("id", models.UUIDField(db_index=True, default=uuid.uuid4)),
                (
                    "problem_status",
                    models.PositiveIntegerField(
                        choices=[
                            (1, "On the border"),
                            (2, "Long term strategic barrier"),
                        ],
                        null=True,
                    ),
                ),
                ("is_resolved", models.NullBooleanField()),
                ("resolved_date", models.DateField(default=None, null=True)),
                ("export_country", models.UUIDField(null=True)),
                ("sectors_affected", models.NullBooleanField()),
                (
                    "sectors",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.UUIDField(),
                        blank=True,
                        default=None,
                        null=True,
                        size=None,
                    ),
                ),
                ("product", models.CharField(max_length=255, null=True)),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("COMPANY", "Company"),
                            ("TRADE", "Trade Association"),
                            ("GOVT", "Government Lead"),
                            ("OTHER", "Other"),
                        ],
                        help_text="chance of success",
                        max_length=25,
                        null=True,
                    ),
                ),
                ("other_source", models.CharField(max_length=255, null=True)),
                ("barrier_title", models.CharField(max_length=255, null=True)),
                ("problem_description", models.TextField(null=True)),
                (
                    "reported_on",
                    models.DateTimeField(blank=True, db_index=True, editable=False),
                ),
                (
                    "status",
                    models.PositiveIntegerField(
                        choices=[
                            (0, "Unfinished"),
                            (1, "Screening"),
                            (2, "Open"),
                            (3, "Rejected"),
                            (4, "Resolved"),
                            (5, "Hibernated"),
                            (6, "Archived"),
                        ],
                        default=0,
                        help_text="status of the barrier instance",
                    ),
                ),
                (
                    "status_summary",
                    models.TextField(
                        default=None,
                        help_text="status summary if provided by user",
                        null=True,
                    ),
                ),
                (
                    "status_date",
                    models.DateTimeField(
                        blank=True,
                        editable=False,
                        help_text="date when status action occurred",
                        null=True,
                    ),
                ),
                (
                    "has_legal_infringement",
                    models.PositiveIntegerField(
                        choices=[(1, "Yes"), (2, "No"), (3, "Don't know")],
                        default=None,
                        help_text="Legal obligations infringed",
                        null=True,
                    ),
                ),
                (
                    "wto_infringement",
                    models.NullBooleanField(
                        default=None, help_text="Legal obligations infringed"
                    ),
                ),
                (
                    "fta_infringement",
                    models.NullBooleanField(
                        default=None, help_text="Legal obligations infringed"
                    ),
                ),
                (
                    "other_infringement",
                    models.NullBooleanField(
                        default=None, help_text="Legal obligations infringed"
                    ),
                ),
                (
                    "infringement_summary",
                    models.TextField(
                        default=None, help_text="Summary of infringments", null=True
                    ),
                ),
                (
                    "political_sensitivities",
                    models.TextField(
                        default=None,
                        help_text="Political sensitivities to be aware of",
                        null=True,
                    ),
                ),
                (
                    "commercial_sensitivities",
                    models.TextField(
                        default=None,
                        help_text="Commercial or confidentiality sensitivities to be aware of",
                        null=True,
                    ),
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
                    "barrier_type",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="metadata.BarrierType",
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
                "verbose_name": "historical barrier instance",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": "history_date",
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalBarrierInteraction",
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
                (
                    "kind",
                    models.CharField(choices=[("COMMENT", "Comment")], max_length=25),
                ),
                ("text", models.TextField(null=True)),
                ("pinned", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
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
                "verbose_name": "historical barrier interaction",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": "history_date",
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalBarrierReportStage",
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
                (
                    "status",
                    models.PositiveIntegerField(
                        choices=[
                            (1, "NOT STARTED"),
                            (2, "IN PROGRESS"),
                            (3, "COMPLETED"),
                        ],
                        null=True,
                    ),
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
                (
                    "stage",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="barriers.Stage",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical barrier report stage",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": "history_date",
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
