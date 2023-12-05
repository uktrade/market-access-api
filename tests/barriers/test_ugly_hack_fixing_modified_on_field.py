import datetime

from django.core import management
from django.test import TestCase

from api.barriers.models import Barrier
from api.core.test_utils import APITestMixin


class TestUglyHackFixingModifiedOnField(APITestMixin, TestCase):
    fixtures = ["barriers", "categories", "users"]

    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier.draft = False
        self.barrier.save()

    def test_modified_on_set_to_value_of_last_history_item_date(self):
        self.barrier.companies = ["1", "2", "3"]
        self.barrier.save()
        # set the modified_on date of the barrier far in the future
        far_future_date = datetime.datetime.now(
            tz=datetime.timezone.utc
        ) + datetime.timedelta(days=365000)
        Barrier.objects.filter(pk=self.barrier.pk).update(modified_on=far_future_date)
        # the following isn't necessary, but makes it possible to inspect the new date when debugging
        self.barrier.refresh_from_db()

        assert self.barrier.modified_on == far_future_date

        management.call_command("ugly_hack_fixing_modified_on_field")
        self.barrier.refresh_from_db()

        assert (
            self.barrier.modified_on
            < Barrier.history.filter(id=self.barrier.pk).first().history_date
        )
