from django.db import DatabaseError


class CheckDatabase:
    """Check the database is up and running."""

    name = 'database'

    def check(self):
        """Perform data check."""
        try:
            # return True for now, will have to change once we have few models in place
            return True, ''
        except DatabaseError as e:
            return False, e


services_to_check = (CheckDatabase, )
