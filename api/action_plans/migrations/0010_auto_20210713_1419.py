# Generated by Django 3.1.12 on 2021-07-13 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('action_plans', '0009_auto_20210713_1350'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionplanmilestone',
            name='completion_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
