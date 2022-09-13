from django.db import migrations

CLEAN_GROWTH_TAG = {
    "Clean Growth": {
        "description": "",
        "order": 7,
        "show_at_reporting": True,
    },
}


def create_clean_growth_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, defaults = CLEAN_GROWTH_TAG.popitem()
    BarrierTag.objects.update_or_create(
        title=title,
        defaults=defaults,
    )


def destroy_clean_growth_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, _ = CLEAN_GROWTH_TAG.popitem()
    BarrierTag.objects.filter(title=title).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0028_international_standards_tag"),
    ]

    operations = [
        migrations.RunPython(
            create_clean_growth_tag, reverse_code=destroy_clean_growth_tag
        ),
    ]
