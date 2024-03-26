from django.db import DatabaseError

from api.barriers.models import Barrier


class CheckDatabase:
    name = "database"

    def check(self):
        try:
            Barrier.objects.exists()
            return True, ""
        except DatabaseError as e:
            return False, e


services_to_check = (CheckDatabase,)
