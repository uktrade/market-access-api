# Generated by Django 2.2.13 on 2020-08-12 08:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("barriers", "0081_auto_20200812_0815"),
        ("wto", "0005_copy_onetoonefield"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="barrierinstance",
            name="wto_profile",
        ),
        migrations.RemoveField(
            model_name="historicalbarrierinstance",
            name="wto_profile",
        ),
    ]
