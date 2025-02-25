from django.db import migrations
from django.db.models import F


def migrate_estimated_resolution_date(apps, schema_editor):
    Barrier = apps.get_model("barriers", "Barrier")
    HistoricalBarrier = apps.get_model("barriers", "HistoricalBarrier")
    EstimatedResolutionDateRequest = apps.get_model("barriers", "EstimatedResolutionDateRequest")
    qs = Barrier.objects.filter(
        estimated_resolution_date__isnull=False,
        proposed_estimated_resolution_date__gt=F('estimated_resolution_date'),
    )
    for barrier in qs:
        historical_record = HistoricalBarrier.objects.filter(
            id=barrier.pk,
            proposed_estimated_resolution_date=barrier.proposed_estimated_resolution_date
        ).order_by("history_date").first()
        EstimatedResolutionDateRequest.objects.create(
            barrier=barrier,
            created_by=historical_record.proposed_estimated_resolution_date_user,
            estimated_resolution_date=historical_record.proposed_estimated_resolution_date,
            reason=barrier.estimated_resolution_date_change_reason,
            status="NEEDS_REVIEW",
            created_on=historical_record.history_date,
            modified_on=historical_record.history_date
        )


class Migration(migrations.Migration):

    dependencies = [
        (
            "barriers",
            "0173_historicalestimatedresolutiondaterequest_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            migrate_estimated_resolution_date, reverse_code=migrations.RunPython.noop
        ),
    ]
