# Generated by Django 3.2.20 on 2023-08-03 14:42

from django.db import migrations

from api.metadata.constants import OrganisationType

ORGANISATIONS = [
    {
        "name": "Department for Culture, Media and Sport",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
]

def create_organisations(apps, schema_editor):
    Organisation = apps.get_model("metadata", "Organisation")

    for item in ORGANISATIONS:
        Organisation.objects.create(**item)


def delete_organisations(apps, schema_editor):
    Organisation = apps.get_model("metadata", "Organisation")

    for item in ORGANISATIONS:
        Organisation.objects.delete(**item)


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0035_auto_20230802_1107'),
    ]

    operations = [
        migrations.RunPython(create_organisations, reverse_code=delete_organisations),
    ]
