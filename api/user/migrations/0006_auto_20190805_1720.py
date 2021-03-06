# Generated by Django 2.2.3 on 2019-08-05 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0005_profile_sso_user_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="sso_user_id",
            field=models.UUIDField(
                help_text="Staff SSO UUID for reference", null=True, unique=True
            ),
        ),
    ]
