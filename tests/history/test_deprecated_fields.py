"""
Sanity tests that fields can be replaced:

TODO: Once approved, remove the fields from legacy history
"""
import datetime

import pytest

from api.barriers.models import Barrier
from api.history.factories import BarrierHistoryFactory

pytestmark = [pytest.mark.django_db]


@pytest.mark.parametrize(
    ("field", "new_value", "old_value"),
    [
        ("commercial_value", 1111, None),
        ("commercial_value_explanation", "wobble", ""),
        ("companies", ["1", "2", "3"], []),
        ("economic_assessment_eligibility", False, None),
        ("economic_assessment_eligibility_summary", "Test", ""),
        ("estimated_resolution_date", datetime.date(year=2030, month=12, day=25), None),
        # ("start_date", datetime.date(year=2030, month=12, day=25), "attr"),  # Works is_summary_sensitive
        ("is_summary_sensitive", True, None),
        ("product", "New", "TEST PRODUCT"),
        ("public_eligibility_summary", "SUMM", ""),
        ("summary", "teeeest", "Some problem description."),
        ("term", 2, 1),
        ("title", "teeeest", "TEST BARRIER"),
    ],
)
def test_simple_fields(draft_barrier, field, new_value, old_value):
    setattr(draft_barrier, field, new_value)
    draft_barrier.save()

    items = BarrierHistoryFactory.get_history_items(barrier_id=draft_barrier.pk)
    data = items[-1].data

    assert data["model"] == "barrier"
    assert data["field"] == field
    assert data["old_value"] == old_value
    assert data["new_value"] == new_value

    v2_history = Barrier.get_history(barrier_id=draft_barrier.id)

    assert v2_history[-1] == data
