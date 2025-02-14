from api.barriers.models import PublicBarrier
from api.collaboration.models import TeamMember
from api.metadata.constants import PublicBarrierStatus


def get_team_members(barrier_id):
    """Helper to return all members for a barrier"""
    return TeamMember.objects.filter(barrier=barrier_id)


def get_team_member_user_ids(barrier_id):
    """
    Helper to return a list of ids for users who are a team member at the given barrier.
    """
    return TeamMember.objects.filter(barrier=barrier_id).values_list(
        "user_id", flat=True
    )


def get_or_create_public_barrier(barrier):
    public_barrier, created = PublicBarrier.objects.get_or_create(
        barrier=barrier,
        defaults={
            "status": barrier.status,
            "status_date": barrier.status_date,
            "country": barrier.country,
            "trading_bloc": barrier.trading_bloc,
            "caused_by_trading_bloc": barrier.caused_by_trading_bloc,
            "sectors": barrier.sectors,
            "all_sectors": barrier.all_sectors,
        },
    )
    return public_barrier, created


def get_published_public_barriers():
    return PublicBarrier.objects.filter(
        _public_view_status=PublicBarrierStatus.PUBLISHED
    )
