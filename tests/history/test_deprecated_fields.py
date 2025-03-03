"""
Sanity tests that fields can be replaced:

TODO: Once approved, remove the fields from legacy history
"""

import pytest

from api.barriers.models import Barrier

pytestmark = [pytest.mark.django_db]


@pytest.mark.parametrize(
    ("field", "new_value", "old_value"),
    [
        ("commercial_value", 1111, None),
        ("commercial_value_explanation", "wobble", ""),
        ("companies", ["1", "2", "3"], []),
        ("economic_assessment_eligibility", False, None),
        ("economic_assessment_eligibility_summary", "Test", ""),
        ("is_summary_sensitive", True, None),
        ("product", "New", "TEST PRODUCT"),
        ("public_eligibility_summary", "SUMM", ""),
        ("summary", "teeeest", "Some problem description."),
        ("term", 2, 1),
        ("title", "teeeest", "TEST BARRIER"),
    ],
)
def test_simple_fields(barrier, field, new_value, old_value):
    setattr(barrier, field, new_value)
    barrier.save()

    v2_history = Barrier.get_history(barrier_id=barrier.id)

    assert v2_history[-1]["model"] == "barrier"
    assert v2_history[-1]["field"] == field
    assert v2_history[-1]["old_value"] == old_value
    assert v2_history[-1]["new_value"] == new_value
