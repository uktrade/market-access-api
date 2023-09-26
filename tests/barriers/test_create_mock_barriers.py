from io import StringIO

from django.core import management
from django.test import TestCase, override_settings

from api.barriers.models import (
    Barrier,
)
from api.core.exceptions import IllegalManagementCommandException
from api.core.test_utils import APITestMixin


class TestDataAnonymise(APITestMixin, TestCase):
    fixtures = [
        "barrier_priorities",
        "barrier_for_anonymisation",
        "categories",
        "users",
    ]

    def call_command(self, quantity, **kwargs):
        out = StringIO()
        management.call_command(
            "create_mock_barriers",
            stdout=out,
            stderr=StringIO(),
            quantity=quantity,
            **kwargs
        )
        return out.getvalue()

    @override_settings(DJANGO_ENV="prod")
    def test_production_run_raises_error(self):
        with self.assertRaises(IllegalManagementCommandException):
            self.call_command(quantity=3)

    def test_barriers_are_created(self):
        current_barrier_count = Barrier.objects.count()
        self.call_command(quantity=3)
        assert Barrier.objects.count() == current_barrier_count + 3

    def test_categories_organisations_included(self):
        self.call_command(quantity=1)
        barrier = Barrier.objects.first()
        assert barrier.categories.count() >= 1
        assert barrier.organisations.count() >= 1
        assert barrier.tags.count() >= 1
        assert barrier.export_types.count() >= 1