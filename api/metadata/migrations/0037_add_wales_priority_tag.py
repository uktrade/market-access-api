from django.db import migrations

WALES_PRIORITY_TAG = {
    "Wales Priority": {
        "description": "",
        "order": 10,
        "show_at_reporting": True,
    }
}


def create_wales_priority_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, defaults = WALES_PRIORITY_TAG.popitem()
    BarrierTag.objects.update_or_create(
        title=title,
        defaults=defaults,
    )


def destroy_wales_priority_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    title, _ = WALES_PRIORITY_TAG.popitem()
    BarrierTag.objects.filter(title=title).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0036_auto_20230803_1442"),
    ]

    operations = [
        migrations.RunPython(
            create_wales_priority_tag, reverse_code=destroy_wales_priority_tag
        ),
    ]
