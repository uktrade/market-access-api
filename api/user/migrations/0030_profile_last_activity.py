# Generated by Django 3.2.15 on 2022-10-17 22:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0029_useractvitiylog'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='last_activity',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]