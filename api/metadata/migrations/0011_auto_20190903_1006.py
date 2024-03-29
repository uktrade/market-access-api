# Generated by Django 2.2.4 on 2019-09-03 10:06

from django.db import migrations

types_to_edit = [
    {
        "old_title": "Intellectual property rights and regulations",
        "new_title": "Unfair application of intellectual property rights and regulations",
    },
]


def edit_barrier_types(apps, schema_editor):
    """
    This change is part of content changes requested by the team
    """
    BarrierType = apps.get_model("metadata", "BarrierType")

    for item in types_to_edit:
        try:
            barrier_type = BarrierType.objects.get(title=item["old_title"])
            barrier_type.title = item["new_title"]
            barrier_type.save()
        except BarrierType.DoesNotExist:
            # ignore any errors
            continue


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0010_auto_20190410_0854"),
    ]

    operations = [
        migrations.RunPython(edit_barrier_types),
    ]
