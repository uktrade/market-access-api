from django.db import migrations, models


def recategorise_public_barrier_statuses(apps, schema_editor):
    """
    Barriers currently with status 60, if they have a title and summary set, move to 70
    otherwise, they move to 20.
    Barriers currently with status 20, if they have a title and summary set, move to 70
    otherwise, they stay at 20.
    """
    PublicBarrierModel = apps.get_model("barriers", "PublicBarrier")
    review_later_barriers = PublicBarrierModel.objects.filter(_public_view_status=60)
    for public_barrier in review_later_barriers:
        if public_barrier._title and public_barrier._summary:
            public_barrier._public_view_status = 70
            public_barrier.save()
        else:
            public_barrier._public_view_status = 20
            public_barrier.save()

    allowed_barriers = PublicBarrierModel.objects.filter(_public_view_status=20)
    for public_barrier in allowed_barriers:
        if public_barrier._title and public_barrier._summary:
            public_barrier._public_view_status = 70
            public_barrier.save()


def undo_recategorisation(apps, schema_editor):
    """
    Barriers in 70 can either go to 60 or 20. Need to loop through all public barriers histories for barriers with 70
    and if the second to last history item has a value of 20 or 60, return them to that status.
    Barriers in 20 can either stay in 20 or move to 60. Need to loop through all public barriers histories for barriers with 20,
    and if the second to last history item has a value of 60, return them to that status.
    """
    PublicBarrierModel = apps.get_model("barriers", "PublicBarrier")
    HistoricalPublicBarrierModel = apps.get_model("barriers", "HistoricalPublicBarrier")

    awaiting_approval_barriers = PublicBarrierModel.objects.filter(
        _public_view_status=70
    )
    for public_barrier in awaiting_approval_barriers:
        history = HistoricalPublicBarrierModel.objects.filter(
            barrier_id=public_barrier.barrier_id
        ).order_by("history_date")
        last_public_view_status = 70
        for history_item in history:
            if history_item._public_view_status != public_barrier._public_view_status:
                last_public_view_status = history_item._public_view_status
                continue
        if last_public_view_status in [60, 20]:
            public_barrier._public_view_status = last_public_view_status
            public_barrier.save()

    eligible_barriers = PublicBarrierModel.objects.filter(_public_view_status=20)
    for public_barrier in eligible_barriers:
        history = HistoricalPublicBarrierModel.objects.filter(
            barrier_id=public_barrier.barrier_id
        ).order_by("history_date")
        last_public_view_status = 20
        for history_item in history:
            if history_item._public_view_status != public_barrier._public_view_status:
                last_public_view_status = history_item._public_view_status
                continue
        if last_public_view_status == 60:
            public_barrier._public_view_status = last_public_view_status
            public_barrier.save()

    migrations.AlterField(
        model_name="historicalpublicbarrier",
        name="_public_view_status",
        field=models.PositiveIntegerField(
            choices=[
                (0, "Not yet sifted"),
                (10, "Not allowed"),
                (20, "Allowed"),
                (30, "Ready"),
                (40, "Published"),
                (50, "Unpublished"),
                (60, "Review later"),
            ],
            default=0,
        ),
    )

    migrations.AlterField(
        model_name="publicbarrier",
        name="_public_view_status",
        field=models.PositiveIntegerField(
            choices=[
                (0, "Not yet sifted"),
                (10, "Not allowed"),
                (20, "Allowed"),
                (30, "Ready"),
                (40, "Published"),
                (50, "Unpublished"),
                (60, "Review later"),
            ],
            default=0,
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "barriers",
            "0161_alter_historicalpublicbarrier__public_view_status_additions",
        ),
    ]

    operations = [
        migrations.RunPython(
            recategorise_public_barrier_statuses, reverse_code=undo_recategorisation
        ),
    ]
