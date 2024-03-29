# Generated by Django 2.2.10 on 2020-04-03 10:50

from django.db import migrations


def update_report_stages(apps, schema_editor):
    BarrierReportStage = apps.get_model("barriers", "BarrierReportStage")
    BarrierReportStage.objects.filter(stage__code="1.1", status=3).update(status=2)


class Migration(migrations.Migration):

    dependencies = [
        ("barriers", "0049_delete_stale_report_stages"),
    ]

    operations = [
        migrations.RunPython(
            update_report_stages, reverse_code=migrations.RunPython.noop
        ),
    ]
