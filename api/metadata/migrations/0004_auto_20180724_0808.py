# Generated by Django 2.0.5 on 2018-07-24 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("metadata", "0003_auto_20180705_1132")]

    operations = [
        migrations.AlterField(
            model_name="barriertype",
            name="category",
            field=models.CharField(
                choices=[("GOODS", "Goods"), ("SERVICES", "Services")], max_length=20
            ),
        )
    ]
