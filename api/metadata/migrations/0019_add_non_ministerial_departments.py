from django.db import migrations

from api.metadata.constants import OrganisationType

ORGANISATIONS = [
    {
        "name": "The Charity Commission",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Competition and Markets Authority",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Crown Prosecution Service",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Food Standards Agency",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Forestry Commission",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Government Actuary's Department",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Government Legal Department",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "HM Land Registry",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "HM Revenue & Customs",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {"name": "NS&I", "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS},
    {
        "name": "The National Archives",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "National Crime Agency",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Office of Rail and Road",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Ofgem",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Ofqual",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Ofsted",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Serious Fraud Office",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "Supreme Court of the United Kingdom",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "UK Statistics Authority",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
    },
    {
        "name": "The Water Services Regulation Authority",
        "organisation_type": OrganisationType.NON_MINISTERIAL_DEPARTMENTS,
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
        ("metadata", "0018_auto_20201118_1133"),
    ]

    operations = [
        migrations.RunPython(create_organisations, reverse_code=delete_organisations),
    ]
