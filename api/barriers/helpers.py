from api.barriers.models import PublicBarrier
from api.collaboration.models import TeamMember


def get_team_members(barrier_id):
    """ Helper to return all members for a barrier """
    return TeamMember.objects.filter(barrier=barrier_id)


def get_team_member_user_ids(barrier_id):
    """
    Helper to return a list of ids for users who area team member at a given barrier.
    """
    return TeamMember.objects.filter(barrier=barrier_id).values_list("user_id", flat=True)


def get_or_create_public_barrier(barrier):
    public_barrier, created = PublicBarrier.objects.get_or_create(
        barrier=barrier,
        defaults={
            "status": barrier.status,
            "country": barrier.export_country,
            "sectors": barrier.sectors,
            "all_sectors": barrier.all_sectors,
        }
    )
    if created:
        public_barrier.categories.set(barrier.categories.all())

    return public_barrier, created
