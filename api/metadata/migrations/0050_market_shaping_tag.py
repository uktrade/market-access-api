from django.db import migrations

MARKET_SHAPING_TAG = {
    "Market Shaping": {
        "description": "",
        "order": 16,
        "show_at_reporting": True,
    }
}


def create_market_shaping_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, defaults = MARKET_SHAPING_TAG.popitem()
    BarrierTag.objects.update_or_create(
        title=title,
        defaults=defaults,
    )


def destroy_market_shaping_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, _ = MARKET_SHAPING_TAG.popitem()
    BarrierTag.objects.filter(title=title).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0049_initial_policy_teams"),
    ]

    operations = [
        migrations.RunPython(
            create_market_shaping_tag,
            reverse_code=destroy_market_shaping_tag,
        ),
    ]
