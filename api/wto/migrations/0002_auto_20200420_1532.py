# Generated by Django 2.2.11 on 2020-04-20 15:32

from django.db import migrations


def create_committees_and_groups(apps, schema_editor):
    WTOCommitteeGroup = apps.get_model("wto", "WTOCommitteeGroup")

    committee_groups = [
        {
            "pk": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "General Council and bodies reporting to it",
        },
        {
            "pk": "2cb189d4-b57f-4869-b7e3-4d898b637b6b",
            "name": "Committees of Plurilateral Agreements",
        },
        {
            "pk": "33049400-2811-418a-863b-2de59f254bda",
            "name": "Bodies established under the Trade Negotiations Committee",
        },
        {
            "pk": "5aeb6715-d472-4a1b-8498-f3e44a877ca4",
            "name": "Subsidiary bodies of the Council for Trade in Services",
        },
        {
            "pk": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Subsidiary bodies of the Council for Trade in Goods",
        },
    ]

    WTOCommitteeGroup.objects.bulk_create(
        [WTOCommitteeGroup(**committee_group) for committee_group in committee_groups]
    )

    WTOCommittee = apps.get_model("wto", "WTOCommittee")

    committees = [
        {
            "pk": "0d4876ab-e125-4167-9449-9f89f843921c",
            "wto_committee_group_id": "5aeb6715-d472-4a1b-8498-f3e44a877ca4",
            "name": "Working Party on GATS Rules",
        },
        {
            "pk": "0fba8aa2-c63c-44b6-a4e1-2f190460b143",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Committee on Regional Trade Agreements",
        },
        {
            "pk": "17044bdc-4506-4eb0-a1a3-39bb257b5657",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Council for Trade in Services",
        },
        {
            "pk": "2667fab0-c8bc-4f9d-a035-0db211510708",
            "wto_committee_group_id": "33049400-2811-418a-863b-2de59f254bda",
            "name": "Negotiating Group on Market Access",
        },
        {
            "pk": "29ca2460-2e5a-4914-bcea-c6074a54d47d",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Dispute Settlement Body",
        },
        {
            "pk": "2b9851b9-08d7-4b44-b271-f729303262be",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Council for Trade-Related Aspects of Intellectual Property Rights",
        },
        {
            "pk": "2de5a9e3-0040-4463-8d9f-e88074142b4d",
            "wto_committee_group_id": "5aeb6715-d472-4a1b-8498-f3e44a877ca4",
            "name": "Committee on Trade in Financial Services",
        },
        {
            "pk": "2ef1e89a-a0bf-4b59-8c84-0df66bf28fab",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Subsidies and Countervailing Measures",
        },
        {
            "pk": "31e180da-e6d7-41b9-9bd9-4ebb4bd8beed",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Committee on Trade and Development",
        },
        {
            "pk": "384ee883-5143-43b5-a909-452b6d8076ea",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Committee on Budget, Finance and Administration",
        },
        {
            "pk": "39958209-e3f7-4603-99f4-20c4073d71b5",
            "wto_committee_group_id": "33049400-2811-418a-863b-2de59f254bda",
            "name": "Committee on Trade and Environment, Special Session",
        },
        {
            "pk": "3f209e66-775f-42f9-91b5-07087f11e251",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Sub-Committee on Least-Developed Countries",
        },
        {
            "pk": "3f99b224-58fa-4cde-ac05-2e9203742ac4",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Trade-Related Investment Measures",
        },
        {
            "pk": "47e98a68-f0cd-4db3-9935-d19f6864e2e8",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Committee on Balance-of-Payments Restrictions",
        },
        {
            "pk": "50fe4100-3788-473b-ab13-b5d828791ed1",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Council for Trade in Goods",
        },
        {
            "pk": "51c71d79-68b5-44c4-b8f1-ea2595e63495",
            "wto_committee_group_id": "33049400-2811-418a-863b-2de59f254bda",
            "name": "Committee on Trade and Development, Special Session",
        },
        {
            "pk": "57971d42-0373-419e-827d-c6148f5aed0a",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Trade Policy Review Body",
        },
        {
            "pk": "5b6f2027-9ca2-40d4-b673-342fcf86108d",
            "wto_committee_group_id": "33049400-2811-418a-863b-2de59f254bda",
            "name": "Sub-Committee on Cotton",
        },
        {
            "pk": "5bce7467-6281-4b91-97f0-a9533924ba26",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Market Access",
        },
        {
            "pk": "6448e88f-bf12-481f-873d-ac1199825743",
            "wto_committee_group_id": "2cb189d4-b57f-4869-b7e3-4d898b637b6b",
            "name": "Committee on Trade in Civil Aircraft",
        },
        {
            "pk": "664d6d42-9dc1-4e34-aac5-f3e28682036f",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Import Licensing",
        },
        {
            "pk": "6ac006d5-2b41-4eb1-a943-6585ad8c1696",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Safeguards",
        },
        {
            "pk": "7d49958c-59de-439f-9270-e1ab02b64898",
            "wto_committee_group_id": "33049400-2811-418a-863b-2de59f254bda",
            "name": "Council for Trade in Services, Special Session",
        },
        {
            "pk": "7e0d6a1d-bba6-438b-a782-38c964edef01",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Technical Barriers to Trade",
        },
        {
            "pk": "7e40bcd0-35ba-482d-af77-106d272d0af6",
            "wto_committee_group_id": "5aeb6715-d472-4a1b-8498-f3e44a877ca4",
            "name": "Committee on Specific Commitments",
        },
        {
            "pk": "8b71d1b8-bfa8-426f-a2e6-793d8311ce4d",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Sanitary and Phytosanitary Measures",
        },
        {
            "pk": "8dc080f0-c5c7-4a2b-90c0-ff3506d6e70e",
            "wto_committee_group_id": "5aeb6715-d472-4a1b-8498-f3e44a877ca4",
            "name": "Working Party on Domestic Regulation",
        },
        {
            "pk": "91c9a28e-a4fd-4706-bf48-8d794a5a57c2",
            "wto_committee_group_id": "33049400-2811-418a-863b-2de59f254bda",
            "name": "Dispute Settlement Body, Special Session",
        },
        {
            "pk": "949cb0ed-5d24-408c-9b3b-35b865933854",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "General Council",
        },
        {
            "pk": "9e1395c6-e506-4ea3-aabe-5f0fc439c2d4",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Trade Negotiations Committee",
        },
        {
            "pk": "ae1c694e-0ad3-4314-a6e9-deabdbfdf402",
            "wto_committee_group_id": "33049400-2811-418a-863b-2de59f254bda",
            "name": "Committee on Agriculture, Special Session",
        },
        {
            "pk": "b1d88dcf-3054-4692-9cba-e896276a8d64",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Committee on Trade Facilitation",
        },
        {
            "pk": "b3319f62-84a2-4712-b52f-bb5e896df739",
            "wto_committee_group_id": "33049400-2811-418a-863b-2de59f254bda",
            "name": "Negotiating Group on Rules",
        },
        {
            "pk": "b3a7b11a-12b5-4f0f-8d50-6a48f6adfdda",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Agriculture",
        },
        {
            "pk": "b5073e1d-e456-414e-afd6-28c2ed6f1078",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Customs Valuation",
        },
        {
            "pk": "c42571c6-8e98-4197-9899-eb6bf53d7215",
            "wto_committee_group_id": "2cb189d4-b57f-4869-b7e3-4d898b637b6b",
            "name": "Committee on Government Procurement",
        },
        {
            "pk": "c9d6b5f3-dd94-4c46-9691-b5c2e428cc0b",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Anti-Dumping Practices",
        },
        {
            "pk": "ca436f37-589c-4010-864f-70de54138deb",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee on Rules of Origin",
        },
        {
            "pk": "d30b6fca-4d0e-4543-bfb9-b4cf1192629f",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Working Group on Trade, Debt and Finance",
        },
        {
            "pk": "e4d87062-6a33-4a4a-8793-d6e946f4345e",
            "wto_committee_group_id": "33049400-2811-418a-863b-2de59f254bda",
            "name": "Council for Trade-Related Aspects of Intellectual Property Rights, Special Session",
        },
        {
            "pk": "f044e1f1-a4a6-4315-a44b-b21d63842d4c",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Committee on Trade and Environment",
        },
        {
            "pk": "f66dd5e8-07e6-4fdf-af4d-621869d3227c",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Committee of Participants on the Expansion of Trade in Information Technology Products",
        },
        {
            "pk": "f88fb335-0cbd-40a9-b33f-735c6278123b",
            "wto_committee_group_id": "f2db8548-64cf-4c2c-82d0-4d6f8fb35e26",
            "name": "Working Party on State Trading Enterprises",
        },
        {
            "pk": "f941441a-a1c2-4f0d-accd-ef7092100df1",
            "wto_committee_group_id": "0a8b978c-efaa-427f-bcaa-18021b3be424",
            "name": "Working Group on Trade and Transfer of Technology",
        },
    ]

    WTOCommittee.objects.bulk_create(
        [WTOCommittee(**committee) for committee in committees]
    )


def delete_committees_and_groups(apps, schema_editor):
    WTOCommittee = apps.get_model("wto", "WTOCommittee")
    WTOCommitteeGroup = apps.get_model("wto", "WTOCommitteeGroup")

    WTOCommittee.objects.all().delete()
    WTOCommitteeGroup.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("wto", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_committees_and_groups, reverse_code=migrations.RunPython.noop
        ),
    ]
