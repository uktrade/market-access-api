from django.db import migrations


COVID_TAG_TITLE = "COVID-19"
BREXIT_TAG_TITLE = "Brexit"

DEFAULT_TAGS = (
    {
        "title": COVID_TAG_TITLE,
        "description": (
            "Barrier imposed because of the COVID-19 (coronavirus) pandemic. "
            "For example restrictions related to medical supplies or food supply chains."
        ),
        "order": 1,
        "show_at_reporting": True,
    },
    {
        "title": BREXIT_TAG_TITLE,
        "description": "",
        "order": 2,
        "show_at_reporting": True,
    },
)


def create_default_tags(apps, schema_editor):
    BarrierTag = apps.get_model("metadata", "BarrierTag")
    for tag in DEFAULT_TAGS:
        try:
            BarrierTag.objects.get(title=tag["title"])
        except BarrierTag.DoesNotExist:
            BarrierTag.objects.create(**tag)


def convert_to_tags(apps, schema_editor):
    """
    Add brexit tag to every barrier where eu_exit_related=1
    """
    BarrierTag = apps.get_model("metadata", "BarrierTag")
    BarrierInstance = apps.get_model("barriers", "BarrierInstance")

    tag = BarrierTag.objects.get(title=BREXIT_TAG_TITLE)
    for barrier in BarrierInstance.objects.filter(eu_exit_related=1):
        barrier.tags.add(tag)


def reverse_convert_to_tags(apps, schema_editor):
    """
    Convert brexit tag back to eu_exit_related
    """
    BarrierTag = apps.get_model("metadata", "BarrierTag")
    BarrierInstance = apps.get_model("barriers", "BarrierInstance")

    tag = BarrierTag.objects.get(title=BREXIT_TAG_TITLE)
    BarrierInstance.objects.filter(tags=tag).update(eu_exit_related=1)


def populate_tags_history(apps, schema_editor):
    """
    Populate tags_cache based on eu_exit_related for all history items
    """
    HistoricalBarrierInstance = apps.get_model("barriers", "HistoricalBarrierInstance")
    BarrierTag = apps.get_model("metadata", "BarrierTag")
    brexit_tag = BarrierTag.objects.get(title=BREXIT_TAG_TITLE)

    HistoricalBarrierInstance.objects.filter(
        eu_exit_related=1
    ).update(
        tags_cache=[brexit_tag.id]
    )


def reverse_tags_history(apps, schema_editor):
    """
    Populate eu_exit_related based on tags_cache for all history items
    """
    HistoricalBarrierInstance = apps.get_model("barriers", "HistoricalBarrierInstance")
    BarrierTag = apps.get_model("metadata", "BarrierTag")
    brexit_tag = BarrierTag.objects.get(title=BREXIT_TAG_TITLE)

    HistoricalBarrierInstance.objects.filter(
        tags_cache__contains=[brexit_tag.id]
    ).update(
        eu_exit_related=1
    )


class Migration(migrations.Migration):
    """
    Converting eu_exit_related field to a tag where applicable.
    """
    dependencies = [
        ('barriers', '0053_historicalbarrierinstance_tags_cache'),
    ]

    operations = [
        migrations.RunPython(create_default_tags, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(convert_to_tags, reverse_code=reverse_convert_to_tags),
        migrations.RunPython(populate_tags_history, reverse_code=reverse_tags_history),
    ]
