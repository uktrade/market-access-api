"""
The generic implementation of historical objects may lead this test module to be able
to parametirze each test case with the model and relevant fields - as opposed to creating
tests for each model.

ie:

@pytest.mark.parametrize(
    ("model", "fields"),
    [
     ("models.Barrier", ["model", ...]),
     ("models.ProgrammeFundProgressUpdate", ["expenditure", ...],
    ]
)
def test_model_history(model, fields):
    .....
"""
import pytest

from api.barriers.models import ProgrammeFundProgressUpdate
from api.history.v2.service import (
    convert_v2_history_to_legacy_object,
    get_model_history,
)
from tests.history.factories import ProgrammeFundProgressUpdateFactory

pytestmark = [pytest.mark.django_db]


def test_model_history(barrier):
    assert ProgrammeFundProgressUpdate.objects.filter(barrier=barrier).count() == 0
    assert ProgrammeFundProgressUpdate.history.filter(barrier=barrier).count() == 0

    ProgrammeFundProgressUpdateFactory(barrier=barrier)

    assert ProgrammeFundProgressUpdate.objects.filter(barrier=barrier).count() == 1
    assert ProgrammeFundProgressUpdate.history.filter(barrier=barrier).count() == 1


def test_new_programme_fund_equal_last_history_item(barrier):
    # sanity check of django history model
    pf = ProgrammeFundProgressUpdateFactory(barrier=barrier)
    pf_historical = ProgrammeFundProgressUpdate.history.get(id=pf.id)

    assert pf.milestones_and_deliverables == pf_historical.milestones_and_deliverables
    assert pf.expenditure == pf_historical.expenditure
    assert pf.barrier == pf_historical.barrier


def test_programme_fund_history_no_history(barrier):
    qs = ProgrammeFundProgressUpdate.history.filter(barrier__id=barrier.id)
    fields = ("milestones_and_deliverables", "expenditure")
    assert (
        get_model_history(qs, model="test", fields=fields, track_first_item=True) == []
    )


def test_create_model(barrier):
    assert ProgrammeFundProgressUpdate.objects.filter(barrier=barrier).count() == 0

    ProgrammeFundProgressUpdateFactory(barrier=barrier)

    assert ProgrammeFundProgressUpdate.objects.filter(barrier=barrier).count() == 1


def test_model_history_not_tracking_first_item(barrier):
    ProgrammeFundProgressUpdateFactory(barrier=barrier)

    qs = ProgrammeFundProgressUpdate.history.filter(barrier__id=barrier.id)
    fields = ("milestones_and_deliverables", "expenditure")

    assert get_model_history(qs, model="test", fields=fields) == []


def test_model_history_tracking_first_item(barrier):
    ProgrammeFundProgressUpdateFactory(barrier=barrier)

    qs = ProgrammeFundProgressUpdate.history.filter(barrier__id=barrier.id)
    fields = ("milestones_and_deliverables", "expenditure")
    model_history = get_model_history(
        qs, model="test", fields=fields, track_first_item=True
    )

    assert ProgrammeFundProgressUpdate.history.count() == 1

    assert model_history == [
        {
            "model": "test",
            "date": model_history[0]["date"],
            "fields": {
                "expenditure": {"new": "Product 5"},
                "milestones_and_deliverables": {"new": "Product 5"},
            },
            "user": {"id": None, "name": None},
        }
    ]


def test_model_history_multiple_items(barrier):
    obj = ProgrammeFundProgressUpdateFactory(
        barrier=barrier, expenditure="A", milestones_and_deliverables="AA"
    )
    obj.milestones_and_deliverables = "BB"
    obj.save()
    obj.refresh_from_db()
    obj.expenditure = "AA"
    obj.milestones_and_deliverables = "CC"
    obj.save()
    obj.refresh_from_db()
    obj.expenditure = "AAA"
    obj.save()

    assert (
        ProgrammeFundProgressUpdate.objects.filter(barrier=barrier, id=obj.id).count()
        == 1
    )
    assert (
        ProgrammeFundProgressUpdate.history.filter(barrier=barrier, id=obj.id).count()
        == 4
    )  # 1 create + 3 updates

    qs = ProgrammeFundProgressUpdate.history.filter(barrier__id=barrier.id, id=obj.id)
    fields = ("milestones_and_deliverables", "expenditure")
    model_history = get_model_history(
        qs, model="test", fields=fields, track_first_item=True
    )

    assert model_history == [
        {
            "model": "test",
            "date": model_history[0]["date"],
            "fields": {
                "expenditure": {"new": "A"},
                "milestones_and_deliverables": {"new": "AA"},
            },
            "user": {"id": None, "name": None},
        },
        {
            "model": "test",
            "date": model_history[1]["date"],
            "fields": {"milestones_and_deliverables": {"new": "BB", "old": "AA"}},
            "user": {"id": None, "name": None},
        },
        {
            "model": "test",
            "date": model_history[2]["date"],
            "fields": {
                "expenditure": {"new": "AA", "old": "A"},
                "milestones_and_deliverables": {"new": "CC", "old": "BB"},
            },
            "user": {"id": None, "name": None},
        },
        {
            "model": "test",
            "date": model_history[3]["date"],
            "fields": {
                "expenditure": {"new": "AAA", "old": "AA"},
            },
            "user": {"id": None, "name": None},
        },
    ]


def test_convert_to_legacy_object(barrier):
    obj = ProgrammeFundProgressUpdateFactory(
        barrier=barrier, expenditure="1", milestones_and_deliverables="arsenal"
    )
    obj.milestones_and_deliverables = "champions"
    obj.save()

    qs = ProgrammeFundProgressUpdate.history.filter(barrier__id=barrier.id)
    fields = ("milestones_and_deliverables", "expenditure")
    model_history = get_model_history(
        qs, model="test", fields=fields, track_first_item=True
    )

    assert ProgrammeFundProgressUpdate.history.count() == 2

    assert model_history == [
        {
            "model": "test",
            "date": model_history[0]["date"],
            "fields": {
                "expenditure": {"new": "1"},
                "milestones_and_deliverables": {"new": "arsenal"},
            },
            "user": {"id": None, "name": None},
        },
        {
            "model": "test",
            "date": model_history[1]["date"],
            "fields": {
                "milestones_and_deliverables": {"new": "champions", "old": "arsenal"},
            },
            "user": {"id": None, "name": None},
        },
    ]

    legacy_representation = convert_v2_history_to_legacy_object(model_history)

    assert legacy_representation[0].data == {
        "date": model_history[0]["date"],
        "field": "milestones_and_deliverables",
        "model": "test",
        "new_value": "arsenal",
        "old_value": None,
        "user": {"id": None, "name": None},
    }

    assert legacy_representation[1].data == {
        "date": model_history[0][
            "date"
        ],  # double model change so shares date of previous
        "field": "expenditure",
        "model": "test",
        "new_value": "1",
        "old_value": None,
        "user": {"id": None, "name": None},
    }

    assert legacy_representation[2].data == {
        "date": model_history[1]["date"],
        "field": "milestones_and_deliverables",
        "model": "test",
        "new_value": "champions",
        "old_value": "arsenal",
        "user": {"id": None, "name": None},
    }
