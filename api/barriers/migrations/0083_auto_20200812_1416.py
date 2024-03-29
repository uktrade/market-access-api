# Generated by Django 2.2.13 on 2020-08-12 14:16

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("barriers", "0082_auto_20200812_0830"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicalbarrierinstance",
            name="categories_cache",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.PositiveIntegerField(),
                blank=True,
                default=list,
                null=True,
                size=None,
            ),
        ),
    ]
