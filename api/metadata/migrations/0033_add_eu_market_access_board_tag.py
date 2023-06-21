from django.db import migrations

EU_MARKET_ACCESS_TAG = {
    "EU Market Access Board": {
        "description": "",
        "order": 9,
        "show_at_reporting": True,
    }
}


def create_eu_market_access_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, defaults = EU_MARKET_ACCESS_TAG.popitem()
    BarrierTag.objects.update_or_create(
        title=title,
        defaults=defaults,
    )


def destroy_eu_market_access_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, _ = EU_MARKET_ACCESS_TAG.popitem()
    BarrierTag.objects.filter(title=title).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0032_add_dbt_organisation"),
    ]

    operations = [
        migrations.RunPython(
            create_eu_market_access_tag, reverse_code=destroy_eu_market_access_tag
        ),
    ]
