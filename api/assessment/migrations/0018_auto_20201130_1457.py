# Generated by Django 3.1.2 on 2020-11-30 14:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("assessment", "0017_remove_user_analysis_data"),
        ("barriers", "0100_merge_20201124_1636"),
        ("history", "0003_rename_assessment"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="economicassessment",
            name="commercial_value",
        ),
        migrations.RemoveField(
            model_name="economicassessment",
            name="commercial_value_explanation",
        ),
        migrations.RemoveField(
            model_name="historicaleconomicassessment",
            name="commercial_value",
        ),
        migrations.RemoveField(
            model_name="historicaleconomicassessment",
            name="commercial_value_explanation",
        ),
    ]
