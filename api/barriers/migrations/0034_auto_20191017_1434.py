# Generated by Django 2.2.4 on 2019-10-17 14:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("barriers", "0033_auto_20190829_1342"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="barrierinstance",
            name="barrier_type",
        ),
        migrations.RemoveField(
            model_name="historicalbarrierinstance",
            name="barrier_type",
        ),
    ]
