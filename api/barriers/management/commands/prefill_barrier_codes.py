from django.conf import settings
from django.core.management import BaseCommand

from api.barriers.models import Barrier
from api.barriers.utils import random_barrier_reference


class Command(BaseCommand):
    help = "Import projects from Data Hub API"

    def _unique_barrier_reference(self):
        """
        function to produce a unique code for a barrier
        making sure it wasn't used earlier
        by randomly picking LENGTH number of characters from CHARSET and
        concatenating them to 2 digit year. If code has already
        been used, repeat until a unique code is found,
        or fail after trying MAX_TRIES number of times.
        """
        loop_num = 0
        unique = False
        while not unique:
            if loop_num < settings.REF_CODE_MAX_TRIES:
                new_code = random_barrier_reference()
                if not Barrier.objects.filter(code=new_code):
                    return new_code
                    unique = True
                loop_num += 1
            else:
                raise ValueError("Error generating a unique reference code.")

    def handle(self, *args, **options):
        empty_instances = Barrier.objects.filter(code__isnull=True)
        for instance in empty_instances:
            new_code = self._unique_barrier_reference()
            instance.code = new_code
            instance.save()
