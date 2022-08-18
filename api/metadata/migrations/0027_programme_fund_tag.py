from django.db import migrations

PROGRAMME_FUND_TAG = {
    "Programme Fund": {
        "description": "",
        "order": 5,
        "show_at_reporting": True,
    },
}


def create_programme_fund_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, defaults = PROGRAMME_FUND_TAG.popitem()
    BarrierTag.objects.update_or_create(
        title=title,
        defaults=defaults,
    )


def destroy_programme_fund_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, _ = PROGRAMME_FUND_TAG.popitem()
    BarrierTag.objects.filter(title=title).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0026_asia_pacific_tag"),
    ]

    operations = [
        migrations.RunPython(
            create_programme_fund_tag, reverse_code=destroy_programme_fund_tag
        ),
    ]
