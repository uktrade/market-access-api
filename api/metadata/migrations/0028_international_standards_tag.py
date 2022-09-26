from django.db import migrations

INTERNATIONAL_STANDARDS_TAG = {
    "International Standards": {
        "description": "",
        "order": 6,
        "show_at_reporting": True,
    },
}


def create_international_standards_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, defaults = INTERNATIONAL_STANDARDS_TAG.popitem()
    BarrierTag.objects.update_or_create(
        title=title,
        defaults=defaults,
    )


def destroy_international_standards_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, _ = INTERNATIONAL_STANDARDS_TAG.popitem()
    BarrierTag.objects.filter(title=title).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0027_programme_fund_tag"),
    ]

    operations = [
        migrations.RunPython(
            create_international_standards_tag,
            reverse_code=destroy_international_standards_tag,
        ),
    ]
