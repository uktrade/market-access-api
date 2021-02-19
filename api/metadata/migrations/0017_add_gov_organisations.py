from django.db import migrations

from api.metadata.constants import OrganisationType

ORGANISATIONS = [
    {
        "name": "Attorney General's Office",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Cabinet Office",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Department for Business, Energy & Industrial Strategy",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Department for Digital, Culture, Media & Sport",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Department for Education",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Department for Environment Food & Rural Affairs",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Department for International Trade",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Department for Transport",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Department for Work & Pensions",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Department of Health & Social Care",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Foreign, Commonwealth & Development Office",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "HM Treasury",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Home Office",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Ministry of Defence",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Ministry of Housing, Communities & Local Government",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Ministry of Justice",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Northern Ireland Office",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Office of the Advocate General for Scotland",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Office of the Leader of the House of Commons",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Office of the Leader of the House of Lords",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Office of the Secretary of State for Scotland",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Office of the Secretary of State for Wales",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "UK Export Finance",
        "organisation_type": OrganisationType.MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Northern Ireland Executive ",
        "organisation_type": OrganisationType.DEVOLVED_ADMINISTRATIONS,
    },
    {
        "name": "The Scottish Government",
        "organisation_type": OrganisationType.DEVOLVED_ADMINISTRATIONS,
    },
    {
        "name": "Welsh Government",
        "organisation_type": OrganisationType.DEVOLVED_ADMINISTRATIONS,
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
        ("metadata", "0016_organisation"),
    ]

    operations = [
        migrations.RunPython(create_organisations, reverse_code=delete_organisations),
    ]
