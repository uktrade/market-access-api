# Generated by Django 3.2.13 on 2022-07-05 08:59

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("action_plans", "0016_populate_action_plans"),
    ]

    operations = [
        migrations.CreateModel(
            name="Stakeholder",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("FRIEND", "Friend"),
                            ("NEUTRAL", "Neutral"),
                            ("TARGET", "Target"),
                            ("BLOCKER", "Blocker"),
                        ],
                        default="NEUTRAL",
                        max_length=7,
                    ),
                ),
                ("organisation", models.TextField(blank=True, default="")),
                ("job_title", models.TextField(blank=True, default="")),
                ("is_organisation", models.BooleanField(default=False)),
                (
                    "action_plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stakeholders",
                        to="action_plans.actionplan",
                    ),
                ),
            ],
            options={
                "ordering": ("name",),
            },
        ),
    ]
