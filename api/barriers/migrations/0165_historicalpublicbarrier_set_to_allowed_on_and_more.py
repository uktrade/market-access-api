# Generated by Django 4.2.11 on 2024-04-22 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("barriers", "0164_historicalpublicbarrier_publishers_summary_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalpublicbarrier",
            name="set_to_allowed_on",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="publicbarrier",
            name="set_to_allowed_on",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
