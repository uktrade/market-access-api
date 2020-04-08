from django.db import migrations
from django.db.models import F


def populate_email_field(apps, schema_editor):
    """
    Many users are missing the email field in the DB.
    Copying the username to the email field if that contains an @ character
    """
    User = apps.get_model("auth", "User")
    User.objects.filter(email__exact="", username__contains="@").update(email=F('username'))


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_auto_20190806_1651'),
    ]

    operations = [
        migrations.RunPython(populate_email_field, reverse_code=migrations.RunPython.noop),
    ]
