from api.collaboration.models import TeamMember


def get_team_members(barrier_id):
    """ Helper to return all members for a barrier """
    return TeamMember.objects.filter(barrier=barrier_id)


def get_team_member_user_ids(barrier_id):
    """
    Helper to return a list of ids for users who area team member at a given barrier.
    """
    return TeamMember.objects.filter(barrier=barrier_id).values_list("user_id", flat=True)
