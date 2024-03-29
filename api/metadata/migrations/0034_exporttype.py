# Generated by Django 3.2.19 on 2023-06-20 20:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_export_types(apps, schema_editor):
    # Get the ExportType model from the apps registry
    ExportType = apps.get_model("metadata", "ExportType")
    # Create the ExportTypes
    ExportType.objects.create(name="goods")
    ExportType.objects.create(name="services")
    ExportType.objects.create(name="investments")


def reverse_create_export_types(apps, schema_editor):
    ExportType = apps.get_model("metadata", "ExportType")
    # Delete the ExportType
    ExportType.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("metadata", "0033_add_eu_market_access_board_tag"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExportType",
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
                ("name", models.CharField(max_length=200, unique=True)),
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
            options={
                "abstract": False,
            },
        ),
        migrations.RunPython(create_export_types, reverse_create_export_types),
    ]
