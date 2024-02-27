import logging
import time
from functools import wraps
from typing import Dict, List, Optional

import numpy
from django.core.cache import cache
from django.db.models import CharField
from django.db.models import Value as V
from django.db.models.functions import Concat
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)


def timing(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = f(*args, **kwargs)
        end = time.perf_counter()
        total_time = end - start
        logger.info(
            f"({__name__}): Function {f.__name__}{args} {kwargs} Took {total_time:.4f} seconds"
        )
        return result

    return wrapper


@timing
def load_transformer():
    return SentenceTransformer("paraphrase-MiniLM-L3-v2")


SIMILARITY_THRESHOLD = 0.19
SIMILAR_BARRIERS_LIMIT = 5
BARRIER_UPDATE_FIELDS = ["title", "summary"]


EMBEDDINGS_CACHE_KEY = "EMBEDDINGS_CACHE_KEY"
BARRIER_IDS_CACHE_KEY = "BARRIER_IDS_CACHE_KEY"


class RelatedBarrierManager:
    __transformer: Optional[SentenceTransformer] = None

    def __init__(self, data: List[Dict]):
        self.__transformer = load_transformer()
        @timing
        def set_data():
            barrier_ids = [str(d["id"]) for d in data]
            barrier_data = [d["barrier_corpus"] for d in data]
            embeddings = self.__transformer.encode(barrier_data, convert_to_tensor=True)
            self.set_embeddings(embeddings.numpy())
            self.set_barrier_ids(barrier_ids)

        if not self.get_barrier_ids() or not isinstance(
            self.get_embeddings(), numpy.ndarray
        ):
            set_data()

    @staticmethod
    def set_embeddings(embeddings):
        cache.set(EMBEDDINGS_CACHE_KEY, embeddings, timeout=None)

    @staticmethod
    def set_barrier_ids(barrier_ids):
        cache.set(BARRIER_IDS_CACHE_KEY, barrier_ids, timeout=None)


    @staticmethod
    def get_embeddings():
        return cache.get(EMBEDDINGS_CACHE_KEY)

    @staticmethod
    def get_barrier_ids():
        return cache.get(BARRIER_IDS_CACHE_KEY)

    @property
    def model(self):
        return self.__transformer

    @timing
    def get_cosine_sim(self):
        embeddings = self.get_embeddings()
        return util.cos_sim(embeddings, embeddings)

    @timing
    def add_barrier(self, barrier):
        barrier_ids = self.get_barrier_ids()
        embeddings = self.get_embeddings()

        @timing
        def encode_barrier_corpus():
            return self.model.encode(
                barrier["barrier_corpus"], convert_to_tensor=True
            ).numpy()

        new_embedding = encode_barrier_corpus()
        new_embeddings = numpy.vstack([embeddings, new_embedding])  # append embedding
        new_barrier_ids = barrier_ids + [barrier["id"]]  # append barrier_id

        self.set_embeddings(new_embeddings)
        self.set_barrier_ids(new_barrier_ids)

    @timing
    def remove_barrier(self, barrier):
        embeddings = self.get_embeddings()
        barrier_ids = self.get_barrier_ids()

        index = None
        for i in range(len(barrier_ids)):
            if barrier_ids[i] == barrier["id"]:
                index = i
                break

        if index is not None:
            # If the barrier exists, delete it from embeddings and barrier ids cache.
            embeddings = numpy.delete(embeddings, index, axis=0)
            del barrier_ids[index]

            self.set_embeddings(embeddings)
            self.set_barrier_ids(barrier_ids)

    @timing
    def update_barrier(self, barrier):
        if barrier["id"] in manager.get_barrier_ids():
            self.remove_barrier(barrier)
        self.add_barrier(barrier)


manager: Optional[RelatedBarrierManager] = None


def get_data() -> List[Dict]:
    from api.barriers.models import Barrier

    return (
        Barrier.objects.filter(archived=False)
        .exclude(draft=True)
        .annotate(
            barrier_corpus=Concat("title", V(". "), "summary", output_field=CharField())
        )
        .values("id", "barrier_corpus")
    )


def init():
    global manager

    if manager:
        raise Exception("DB already set, please stop db or restart application")

    data = get_data()  # List[Dict]
    manager = RelatedBarrierManager(data)


@timing
def get_similar_barriers(barrier: Dict):
    if not manager:
        raise Exception("Related Barrier DB not set")

    if barrier["id"] not in manager.get_barrier_ids():
        manager.add_barrier(barrier)

    barrier_ids = manager.get_barrier_ids()
    cosine_sim = manager.get_cosine_sim()

    index = None
    for i, barrier_id in enumerate(barrier_ids):
        if barrier_id == barrier['id']:
            index = i
            break

    scores = cosine_sim[index]
    barrier_scores = dict(zip(barrier_ids, scores))
    barrier_scores = {k: v for k, v in barrier_scores.items() if v > SIMILARITY_THRESHOLD and k != barrier['id']}
    barrier_scores = sorted(barrier_scores.items(), key=lambda x: x[1])[-SIMILAR_BARRIERS_LIMIT:]

    return [b[0] for b in barrier_scores]


def barrier_to_corpus(barrier):
    return barrier.title + ". " + barrier.summary
