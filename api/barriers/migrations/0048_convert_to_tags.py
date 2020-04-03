from django.db import migrations

BREXIT_TAG_TITLE = "brexit"
DEFAULT_TAGS = [
    {
        "title": BREXIT_TAG_TITLE,
        "description": "",
        "show_at_reporting": True,
    },
    {
        "title": "covid-19",
        "description": "Use to indicate any barrier or measure taken in response to the Covid-19 crisis. \
                       For example restrictions related to medical supplies or food supply chains.",
        "show_at_reporting": True,
    },
]


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
    for barrier in BarrierInstance.objects.raw('SELECT * FROM barriers_barrierinstance WHERE eu_exit_related=1'):
        barrier.tags.add(tag)


class Migration(migrations.Migration):
    """
    Non reversible migration - converting eu_exit_related field to a tag where applicable
    """
    dependencies = [
        ('barriers', '0047_auto_20200331_0643'),
    ]

    operations = [
        migrations.RunPython(create_default_tags, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(convert_to_tags, reverse_code=migrations.RunPython.noop),
    ]
