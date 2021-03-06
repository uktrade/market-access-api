# Generated by Django 3.1.2 on 2020-11-05 17:11

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assessment", "0011_convert_null_to_empty"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assessment",
            name="archived_reason",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="assessment",
            name="commercial_value",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="assessment",
            name="commercial_value_explanation",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="assessment",
            name="explanation",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="assessment",
            name="export_value",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="assessment",
            name="impact",
            field=models.CharField(
                blank=True,
                choices=[
                    ("HIGH", "High"),
                    ("MEDIUMHIGH", "Medium High"),
                    ("MEDIUMLOW", "Medium Low"),
                    ("LOW", "Low"),
                ],
                default="",
                max_length=25,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="assessment",
            name="import_market_size",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="assessment",
            name="value_to_economy",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="historicalassessment",
            name="archived_reason",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalassessment",
            name="commercial_value",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="historicalassessment",
            name="commercial_value_explanation",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="historicalassessment",
            name="documents_cache",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.JSONField(), blank=True, default=list, size=None
            ),
        ),
        migrations.AlterField(
            model_name="historicalassessment",
            name="explanation",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalassessment",
            name="export_value",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="historicalassessment",
            name="impact",
            field=models.CharField(
                blank=True,
                choices=[
                    ("HIGH", "High"),
                    ("MEDIUMHIGH", "Medium High"),
                    ("MEDIUMLOW", "Medium Low"),
                    ("LOW", "Low"),
                ],
                default="",
                max_length=25,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalassessment",
            name="import_market_size",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="historicalassessment",
            name="value_to_economy",
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="historicalresolvabilityassessment",
            name="archived_reason",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalstrategicassessment",
            name="archived_reason",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="resolvabilityassessment",
            name="archived_reason",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="strategicassessment",
            name="archived_reason",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
    ]
