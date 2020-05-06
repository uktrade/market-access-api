from django.db import migrations

CONTRIBUTOR = "Contributor"
OWNER = "Owner"
REPORTER = "Reporter"


def add_missing_reporters_and_collaborators(apps, schema_editor):
    BarrierInstance = apps.get_model('barriers', 'BarrierInstance')
    HistoricalBarrierInstance = apps.get_model('barriers', 'HistoricalBarrierInstance')
    TeamMember = apps.get_model('collaboration', 'TeamMember')
    HistoricalTeamMember = apps.get_model('collaboration', 'HistoricalTeamMember')
    for barrier in BarrierInstance.objects.all():
        # Reporters
        if barrier.created_by:
            team_member, created = TeamMember.objects.get_or_create(
                barrier=barrier,
                user=barrier.created_by,
                role=REPORTER,
                defaults={
                    "default": True,
                }
            )
            if created:
                HistoricalTeamMember.objects.create(
                    id=team_member.id,
                    history_date=barrier.created_on,
                    barrier=barrier,
                    user=barrier.created_by,
                    role=REPORTER,
                    default=True
                )
        # Contributors
        history_records = HistoricalBarrierInstance.objects.filter(id=barrier.id)
        for history_record in history_records:
            if history_record.history_user:
                try:
                    team_member, created = TeamMember.objects.get_or_create(
                        barrier=barrier,
                        user=history_record.history_user,
                        defaults={
                            "role": CONTRIBUTOR,
                        }
                    )
                    if created:
                        HistoricalTeamMember.objects.create(
                            id=team_member.id,
                            history_date=history_record.history_date,
                            barrier=barrier,
                            user=history_record.history_user,
                            role=CONTRIBUTOR,
                        )
                except TeamMember.MultipleObjectsReturned:
                    # The user is already a team member (multiple times)
                    # Or, the user got removed from the team before (and has been archived)
                    # in which case there's no need to add them back in to the team
                    pass


def add_reporter_as_owner(apps, schema_editor):
    TeamMember = apps.get_model('collaboration', 'TeamMember')
    HistoricalTeamMember = apps.get_model('collaboration', 'HistoricalTeamMember')
    # Tidy up existing owners
    #   1 - Unify casing of Owner members across the records
    #   2 - make Owners default members so they cannot be deleted
    TeamMember.objects.filter(role__iexact=OWNER).update(default=True, role=OWNER)
    HistoricalTeamMember.objects.filter(role__iexact=OWNER).update(role=OWNER)
    # Add an owner member to the barriers that don't have one
    barrier_ids = TeamMember.objects.filter(role__iexact=OWNER).values_list("barrier_id", flat=True)
    reporters = TeamMember.objects.filter(role=REPORTER).exclude(barrier__in=barrier_ids)
    for reporter in reporters:
        team_member = TeamMember.objects.create(
            barrier=reporter.barrier,
            user=reporter.user,
            role=OWNER,
            default=True
        )
        HistoricalTeamMember.objects.create(
            id=team_member.id,
            history_date=reporter.created_on,
            barrier=reporter.barrier,
            user=reporter.user,
            role=OWNER,
            default=True
        )


def convert_to_contributors(apps, schema_editor):
    """
    Convert all existing team members to contributors
    apart from reporters and potential owners.
    """
    TeamMember = apps.get_model('collaboration', 'TeamMember')
    HistoricalTeamMember = apps.get_model('collaboration', 'HistoricalTeamMember')
    TeamMember.objects.exclude(role__in=(REPORTER, OWNER)).update(role=CONTRIBUTOR)
    HistoricalTeamMember.objects.exclude(role__in=(REPORTER, OWNER)).update(role=CONTRIBUTOR)


class Migration(migrations.Migration):
    dependencies = [
        ('collaboration', '0004_change_creator_to_reporter'),
    ]
    operations = [
        migrations.RunPython(
            add_missing_reporters_and_collaborators,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            add_reporter_as_owner,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            convert_to_contributors,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
