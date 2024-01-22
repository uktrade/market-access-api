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
from datetime import datetime

import pytest

from api.barriers.models import (
    Barrier,
    BarrierNextStepItem,
    BarrierProgressUpdate,
    ProgrammeFundProgressUpdate,
)
from api.history.v2.service import (
    convert_v2_history_to_legacy_object,
    get_model_history,
)
from api.metadata.constants import PROGRESS_UPDATE_CHOICES
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
    assert get_model_history(qs, model="test", fields=fields) == []


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
    ProgrammeFundProgressUpdateFactory(
        barrier=barrier, milestones_and_deliverables="a", expenditure="b"
    )

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
            "field": "milestones_and_deliverables",
            "user": None,
            "old_value": None,
            "new_value": "a",
        },
        {
            "model": "test",
            "date": model_history[0]["date"],
            "field": "expenditure",
            "user": None,
            "old_value": None,
            "new_value": "b",
        },
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
    model_history = get_model_history(qs, model="test", fields=fields)

    assert model_history == [
        {
            "date": model_history[0]["date"],
            "field": "milestones_and_deliverables",
            "model": "test",
            "new_value": "BB",
            "old_value": "AA",
            "user": None,
        },
        {
            "date": model_history[1]["date"],
            "field": "milestones_and_deliverables",
            "model": "test",
            "new_value": "CC",
            "old_value": "BB",
            "user": None,
        },
        {
            "date": model_history[2]["date"],
            "field": "expenditure",
            "model": "test",
            "new_value": "AA",
            "old_value": "A",
            "user": None,
        },
        {
            "date": model_history[3]["date"],
            "field": "expenditure",
            "model": "test",
            "new_value": "AAA",
            "old_value": "AA",
            "user": None,
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
    assert len(model_history) == 3

    v2_to_legacy = convert_v2_history_to_legacy_object(model_history)

    assert hasattr(v2_to_legacy[0], "data")
    assert hasattr(v2_to_legacy[1], "data")
    assert hasattr(v2_to_legacy[2], "data")


def test_barrier_status_history(barrier):
    barrier.status = 4
    barrier.status_date = datetime(2020, 5, 1)
    barrier.save()

    items = Barrier.get_history(barrier_id=barrier.pk)
    data = items[-1]

    assert data == {
        "date": data["date"],
        "field": "status",
        "model": "barrier",
        "new_value": {
            "status": 4,
            "status_date": data["new_value"]["status_date"],
            "status_summary": "",
            "sub_status": "",
            "sub_status_other": "",
        },
        "old_value": {
            "status": 1,
            "status_date": data["old_value"]["status_date"],
            "status_summary": "",
            "sub_status": "",
            "sub_status_other": "",
        },
        "user": None,
    }


def test_barrier_next_step_item_history(barrier):
    assert BarrierNextStepItem.objects.filter(barrier=barrier).count() == 0

    obj = BarrierNextStepItem.objects.create(barrier=barrier, next_step_item="Tests")
    obj.next_step_item = "Updated Tests"
    obj.save()

    history = BarrierNextStepItem.get_history(barrier_id=barrier.id)

    assert history == [
        {
            "date": history[0]["date"],
            "field": "next_step_item",
            "model": "barrier_next_step_item",
            "new_value": "Updated Tests",
            "old_value": "Tests",
            "user": None,
        }
    ]
    assert BarrierNextStepItem.objects.filter(barrier=barrier).count() == 1


def test_progress_update_next_steps(barrier):
    # Ensure history returns a "created" progress update and a subsequent edit
    progress_update = BarrierProgressUpdate.objects.create(
        barrier=barrier,
        status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
        update="Nothing Specific",
        next_steps="First steps",
    )
    progress_update.next_steps = "Edited Steps"
    progress_update.save()

    items = BarrierProgressUpdate.get_history(barrier_id=barrier.id)

    assert items[-1] == {
        "date": items[-1]["date"],
        "field": "status",
        "model": "progress_update",
        "new_value": {
            "next_steps": "Edited Steps",
            "status": "ON_TRACK",
            "update": "Nothing Specific",
        },
        "old_value": {
            "next_steps": "First steps",
            "status": "ON_TRACK",
            "update": "Nothing Specific",
        },
        "user": None,
    }
