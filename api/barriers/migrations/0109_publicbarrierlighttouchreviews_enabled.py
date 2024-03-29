# Generated by Django 3.1.8 on 2021-05-10 19:05

from django.db import migrations, models


def update_enable_status_by_saving_public_barriers(apps, schema_editor):
    PublicBarrierLightTouchReviews = apps.get_model(
        "barriers", "PublicBarrierLightTouchReviews"
    )
    for item in PublicBarrierLightTouchReviews.objects.all():
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        (
            "barriers",
            "0108_publicbarrierlighttouchreviews_missing_government_organisation_approvals",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="publicbarrierlighttouchreviews",
            name="enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(update_enable_status_by_saving_public_barriers),
    ]
