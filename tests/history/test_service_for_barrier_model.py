import pytest

from api.barriers.models import Barrier

pytestmark = [pytest.mark.django_db]


def test_draft_barrier_history(draft_barrier):
    assert Barrier.get_history(barrier_id=draft_barrier.id) == []


def test_archive_barrier(user, barrier):
    """
    barrier fixture calls .submit_report() which alters model
    """
    barrier.archive(user=user, reason="DUPLICATE", explanation="Already exists")

    history = Barrier.get_history(barrier_id=barrier.id)

    assert history[-1] == {
        "date": history[-1]["date"],
        "field": "archived",
        "model": "barrier",
        "new_value": {
            "archived": True,
            "archived_explanation": "Already exists",
            "archived_reason": "DUPLICATE",
            "unarchived_reason": "",
        },
        "old_value": {
            "archived": False,
            "archived_explanation": "",
            "archived_reason": "",
            "unarchived_reason": "",
        },
        "user": None,
    }
