from typing import Dict, List, Tuple

import pytest
import torch
from django.db.models import signals
from factory.django import mute_signals
from sentence_transformers import SentenceTransformer

from api.barriers.models import Barrier
from api.related_barriers.constants import BarrierEntry
from api.related_barriers.manager import RelatedBarrierManager, barrier_to_corpus
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def manager(settings):
    # Loads transformer model
    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
    return RelatedBarrierManager()


@pytest.fixture
def TEST_CASE_1() -> Tuple[List[Dict], List[Barrier]]:
    with mute_signals(signals.pre_save):
        b1 = BarrierFactory(title="The weather is lovely today", summary="")
        b2 = BarrierFactory(title="It's so sunny outside!", summary="")
        b3 = BarrierFactory(title="He drove to the stadium.", summary="")

    data = (
        Barrier.objects.filter(archived=False)
        .exclude(draft=True)
        .values("id", "title", "summary")
    )

    return [
        {"id": str(d["id"]), "barrier_corpus": f"{d['title']} . {d['summary']}"}
        for d in data
    ], [b1, b2, b3]


@pytest.fixture
def TEST_CASE_2() -> Tuple[List[Dict], List[Barrier]]:
    corpus = [
        "A man is eating food.",
        "A man is eating a piece of bread.",
        "The girl is carrying a baby.",
        "A man is riding a horse.",
        "A woman is playing violin.",
        "Two men pushed carts through the woods.",
        "A man is riding a white horse on an enclosed ground.",
        "A monkey is playing drums.",
        "A cheetah is running behind its prey.",
    ]
    with mute_signals(signals.pre_save):
        barriers = [BarrierFactory(title=title) for title in corpus]

    data = (
        Barrier.objects.filter(archived=False).exclude(draft=True).values("id", "title")
    )

    return [
        {"id": str(d["id"]), "barrier_corpus": f"{d['title']}"} for d in data
    ], barriers


@pytest.fixture
def TEST_CASE_3() -> Tuple[List[Dict], List[Barrier]]:
    barriers = [
        BarrierFactory(
            title="Translating Trademark for Whisky Products in Quebec",
            summary=(
                "Bill 96, published by the Quebec Government years ago, changed "
                "general regulation regarding French language translations. They "
                "ask business to translate everything into French, including trademarks "
                "which causes particular difficulties. SWA are waiting for a regulation "
                "on the implementation of this as there is a lack of clarity where in "
                "the draft regulation they stated that trademarks are exempted but if it "
                "includes a general term or description of the product, this should be translated.",
            ),
        ),
        BarrierFactory(
            title="Offshore wind: local content; skills & workforce engagement",
            summary=(
                "Taiwan requested local content for offshore wind project but Taiwanese "
                "firms currently lack capabilities and experience, which combined with "
                "weak domestic competition, has in many cases resulted in inflated costs "
                "and unnecessary project delays. In 2021, Taiwan Energy Administration "
                "allowed some additional flexibility as developers only needed to source "
                "60% of items locally, compared to 100% previously. This removes the "
                "absolute market access barrier but still not enough.",
            ),
        ),
    ]

    return [
        {"id": str(b.id), "barrier_corpus": f"{b.title} . {b.summary}"}
        for b in barriers
    ], barriers


def test_transformer_loads(manager):
    assert isinstance(manager.model, SentenceTransformer)


def test_search_case_1(manager, TEST_CASE_1):
    training_data, barriers = TEST_CASE_1

    b1, b2, b3 = barriers

    manager.set_data(training_data)

    assert set(manager.get_barrier_ids()) == set([str(b.id) for b in barriers])

    results1 = manager.get_similar_barriers_searched(
        search_term="The weather",
        similarity_threshold=0,
        quantity=5,
    )
    results2 = manager.get_similar_barriers_searched(
        search_term="A car at the stadium",
        similarity_threshold=0,
        quantity=5,
    )

    assert results1 == [
        (str(b3.id), torch.tensor(0.1963)),
        (str(b2.id), torch.tensor(0.5966)),
        (str(b1.id), torch.tensor(0.6943)),
    ]
    assert results2 == [
        (str(b1.id), torch.tensor(0.1044)),
        (str(b2.id), torch.tensor(0.1335)),
        (str(b3.id), torch.tensor(0.6433)),
    ]


def test_search_case_2(manager, TEST_CASE_2):
    training_data, barriers = TEST_CASE_2

    manager.set_data(training_data)

    assert set(manager.get_barrier_ids()) == set([str(b.id) for b in barriers])

    results1 = manager.get_similar_barriers_searched(
        search_term="A man is eating pasta.",
        similarity_threshold=0,
        quantity=20,
    )

    assert results1 == [
        (str(barriers[4].id), torch.tensor(0.0336)),
        (str(barriers[7].id), torch.tensor(0.0819)),
        (str(barriers[8].id), torch.tensor(0.0980)),
        (str(barriers[6].id), torch.tensor(0.1047)),
        (str(barriers[3].id), torch.tensor(0.1889)),
        (str(barriers[1].id), torch.tensor(0.5272)),
        (str(barriers[0].id), torch.tensor(0.7035)),
    ]


def test_related_barriers_1(manager, TEST_CASE_3):
    training_data, barriers = TEST_CASE_3

    manager.set_data(training_data)

    assert set(manager.get_barrier_ids()) == set([str(b.id) for b in barriers])

    barrier_entry = BarrierEntry(
        id=str(barriers[0].id), barrier_corpus=barrier_to_corpus(barriers[0])
    )
    results1 = manager.get_similar_barriers(
        barrier_entry,
        similarity_threshold=0,
        quantity=20,
    )

    assert results1 == [(str(barriers[1].id), torch.tensor(0.1556))]
