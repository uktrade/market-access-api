# Generated by Django 3.1.2 on 2020-10-12 13:47

from django.db import migrations

TAGS = {
    "TOP-PRIORITY BARRIER": {
        "id": 4,
        "description": "Indicator that the barrier is marked as a top priority for resolution.",
        "order": 4,
        "show_at_reporting": True,
    },
}


def create_top_priority_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")

    for title, defaults in TAGS.items():
        BarrierTag.objects.update_or_create(
            title=title,
            defaults=defaults,
        )


def delete_top_priority_tag(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")
    BarrierTag.objects.filter(title="Top Priority").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0020_add_more_organisations"),
    ]

    operations = [
        migrations.RunPython(create_top_priority_tag, reverse_code=delete_top_priority_tag),
    ]