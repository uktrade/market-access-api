# Generated by Django 3.2.23 on 2023-12-11 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("barriers", "0156_auto_20231205_1710"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalpublicbarrier",
            name="changed_since_public",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="publicbarrier",
            name="changed_since_public",
            field=models.BooleanField(default=False),
        ),
    ]
