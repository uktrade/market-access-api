# Generated by Django 3.2.20 on 2023-09-18 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feedback", "0003_feedback_experienced_issues"),
    ]

    operations = [
        migrations.AddField(
            model_name="feedback",
            name="other_detail",
            field=models.TextField(blank=True, default=""),
        ),
    ]
