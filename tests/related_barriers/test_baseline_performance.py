from typing import Dict, List, Tuple

import pytest
import torch
from django.db.models import signals
from factory.django import mute_signals
from sentence_transformers import SentenceTransformer

from api.barriers.models import Barrier
from api.related_barriers.constants import BarrierEntry
from api.related_barriers.manager import barrier_to_corpus
from tests.barriers.factories import BarrierFactory

pytestmark = [pytest.mark.django_db]


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


def test_stopwords_lose_semantic_meaning(transformer, stop_words):
    """
    This test shows that removing stopwords can affect the semantic meaning of a sentence as interpreted by
    the transformer model.

    Results:
        Including stopwords - [0.8278, 0.8852] - ie scores of [data[0], data[1]]
        Removing stopwords - [0.8992, 0.8992] - ie scores of [data_no_stopwords[0], data_no_stopwords[1]]

    The results show that the model understands the honey preference of the bear which
    is linguistically determined by the stop words: {does, not}.

    Including the stopwords shows a higher correlation between the search_phrase and data[1], which is expected.
    Removing the stopwords renders the 2 phrases the same, so the results are identical. The semantic value of the
    bear's honey preference is lost with the removal of the stopword.
    """
    data = [
        "a bear does not like to eat the honey",
        "the bear does like to eat the honey",
    ]
    data_no_stopwords = [
        " ".join(word for word in d.split(" ") if word not in stop_words) for d in data
    ]

    search_phrases = ["bear that eats honey"]

    data_embeddings = transformer.encode(
        data + search_phrases, convert_to_tensor=True
    ).numpy()
    data_no_stopwords_embeddings = transformer.encode(
        data_no_stopwords + search_phrases, convert_to_tensor=True
    ).numpy()

    cosine_sim = transformer.similarity(data_embeddings, data_embeddings)
    cosine_sim_no_stopwords = transformer.similarity(
        data_no_stopwords_embeddings, data_no_stopwords_embeddings
    )

    search_similarity = cosine_sim[2][:2].round(decimals=4)
    search_similarity_no_stopwords = cosine_sim_no_stopwords[2][:2].round(decimals=4)

    assert torch.equal(search_similarity, torch.Tensor([0.8427, 0.8852]))
    assert torch.equal(search_similarity_no_stopwords, torch.Tensor([0.8992, 0.8992]))


def test_country_keywords(transformer):
    """
    The results show the Country keyword impacts the similarity score.
    """
    data = [
        "This barrier relates to the export of wine to Malaysia.",
        "This barrier relates to the export of wine to China",
    ]

    search_phrases = ["Wine exports", "Wine exports Malaysia", "China barrier"]

    data_embeddings = transformer.encode(
        data + search_phrases, convert_to_tensor=True
    ).numpy()

    cosine_sim = transformer.similarity(data_embeddings, data_embeddings)

    search_results = [
        cosine_sim[2][:2].round(decimals=4),
        cosine_sim[3][:2].round(decimals=4),
        cosine_sim[4][:2].round(decimals=4),
    ]

    assert torch.equal(
        search_results[0], torch.Tensor([0.6763, 0.6826])
    )  # search_phrases[0]
    assert torch.equal(
        search_results[1], torch.Tensor([0.8406, 0.6639])
    )  # search_phrases[1]
    assert torch.equal(
        search_results[2], torch.Tensor([0.3886, 0.5383])
    )  # search_phrases[2]
