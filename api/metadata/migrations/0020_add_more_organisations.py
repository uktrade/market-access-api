from django.db import migrations

from api.metadata.constants import OrganisationType


ORGANISATIONS = [
    {
        "name": "Ofcom",
        "organisation_type": OrganisationType.AGENCIES_AND_OTHER_PUBLIC_BODIES,
    },
    {
        "name": "Intellectual Property Office",
        "organisation_type": OrganisationType.AGENCIES_AND_OTHER_PUBLIC_BODIES,
    },
    {
        "name": "Medicines and Healthcare products Regulatory Agency",
        "organisation_type": OrganisationType.AGENCIES_AND_OTHER_PUBLIC_BODIES,
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
        ("metadata", "0019_add_non_ministerial_departments"),
    ]

    operations = [
        migrations.RunPython(create_organisations, reverse_code=delete_organisations),
    ]
