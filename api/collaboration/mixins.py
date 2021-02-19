from api.collaboration.models import TeamMember


class TeamMemberModelMixin:
    """
    Mixin to be used at views.
    """

    def update_contributors(self, barrier):
        if self.request.user:
            try:
                TeamMember.objects.get_or_create(
                    barrier=barrier,
                    user=self.request.user,
                    defaults={
                        "role": TeamMember.CONTRIBUTOR,
                        "created_by": self.request.user,
                    },
                )
            except TeamMember.MultipleObjectsReturned:
                # There might be multiple members associated with the user (e.g. Reporter/Owner)
                pass
