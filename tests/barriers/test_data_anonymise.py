from django.core import management
from django.test import TestCase

# from api.barriers.models import Barrier
from api.core.test_utils import APITestMixin

# from api.history.factories import BarrierHistoryFactory


class TestDataAnonymise(APITestMixin, TestCase):
    fixtures = ["barriers", "categories", "users"]

    def setUp(self):
        super().setUp()
        # self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        # self.barrier.save()

        # Set todays date to use as argument for management command for 'barrier_cutoff_date'
        self.todays_date = ""

    def test_production_run_raises_error(self):

        # Override setting DJANGO_ENV to be "prod"

        # Run management command
        management.call_command(
            f"data_anonymise --barrier_cutoff_date {self.todays_date}"
        )

        # Assert error raised with correct message
        # assert self.barrier.modified_on == most_recent_history_item["date"]

    def test_completed_barrier_anonymised(self):

        # Create barrier with all fields populated, including fields that will not be
        # anonymised

        # Run management command
        management.call_command(
            f"data_anonymise --barrier_cutoff_date {self.todays_date}"
        )

        # Assert fields have been anonymised

        # Assert history has been wiped

        # Assert other fields have been left alone

    def test_required_barried_anonymised(self):

        # Create barrier with only required fields all barriers will have populated

        # Run management command
        management.call_command(
            f"data_anonymise --barrier_cutoff_date {self.todays_date}"
        )

        # Assert required fields have been anonymised

        # Assert history has been wiped

        # Assert optional fields have been left blank/empty
