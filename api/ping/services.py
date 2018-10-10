from api.barriers.models import BarrierInstance
from django.db import DatabaseError


class CheckDatabase:
    """Check the database is up and running."""

    name = "database"

    def check(self):
        """Perform data check."""
        try:
            BarrierInstance.objects.all().exists()
            return True, ""
        except DatabaseError as e:
            return False, e


services_to_check = (CheckDatabase,)
