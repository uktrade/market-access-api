from django.db import migrations

from api.metadata.constants import OrganisationType

ORGANISATIONS = [
    {
        "name": "Department for Business and Trade",
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
        ("metadata", "0031_alter_asia_pacfic_tag"),
    ]

    operations = [
        migrations.RunPython(create_organisations, reverse_code=delete_organisations),
    ]
