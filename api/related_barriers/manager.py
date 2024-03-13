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

from api.related_barriers.constants import BarrierEntry

logger = logging.getLogger(__name__)


def timing(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = f(*args, **kwargs)
        end = time.perf_counter()
        total_time = end - start
        logger.info(f"({__name__}{f.__name__}): {total_time:.4f} seconds")
        return result

    return wrapper


@timing
def get_transformer():
    return SentenceTransformer("paraphrase-MiniLM-L3-v2")


BARRIER_UPDATE_FIELDS: List[str] = ["title", "summary"]


EMBEDDINGS_CACHE_KEY = "EMBEDDINGS_CACHE_KEY"
BARRIER_IDS_CACHE_KEY = "BARRIER_IDS_CACHE_KEY"


class SingletonMeta(type):
    """
    Related Barrier Manager is a Singleton class to manage a ~30MB
    transformer and it's application use case for DMAS.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class RelatedBarrierManager(metaclass=SingletonMeta):
    __transformer: Optional[SentenceTransformer] = None

    def __str__(self):
        return "Related Barrier Manager"

    def __init__(self, data: List[Dict]):
        """
        Only called once in a execution lifecycle
        """
        self.__transformer = get_transformer()

        @timing
        def set_data():
            """
            Load data into memory.
            """
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
    def flush():
        cache.delete(EMBEDDINGS_CACHE_KEY)
        cache.delete(BARRIER_IDS_CACHE_KEY)

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
    def encode_barrier_corpus(self, barrier: BarrierEntry):
        return self.model.encode(barrier.barrier_corpus, convert_to_tensor=True).numpy()

    @timing
    def add_barrier(
        self, barrier: BarrierEntry, barrier_ids: Optional[List[str]] = None
    ):
        """barrier_ids: optimisation flag to avoid multiple cache requests"""
        if barrier_ids is None:
            barrier_ids = self.get_barrier_ids()
        embeddings = self.get_embeddings()

        new_embedding = self.encode_barrier_corpus(barrier)
        new_embeddings = numpy.vstack([embeddings, new_embedding])  # append embedding
        new_barrier_ids = barrier_ids + [barrier.id]  # append barrier_id

        self.set_embeddings(new_embeddings)
        self.set_barrier_ids(new_barrier_ids)

    @timing
    def remove_barrier(self, barrier: BarrierEntry, barrier_ids=None):
        embeddings = self.get_embeddings()
        if not barrier_ids:
            barrier_ids = self.get_barrier_ids()

        index = None
        for i in range(len(barrier_ids)):
            if barrier_ids[i] == barrier.id:
                index = i
                break

        if index is not None:
            # If the barrier exists, delete it from embeddings and barrier ids cache.
            embeddings = numpy.delete(embeddings, index, axis=0)
            del barrier_ids[index]

            self.set_embeddings(embeddings)
            self.set_barrier_ids(barrier_ids)

    @timing
    def update_barrier(self, barrier: BarrierEntry):
        barrier_ids = manager.get_barrier_ids()
        if barrier.id in barrier_ids:
            self.remove_barrier(barrier, barrier_ids)
        self.add_barrier(barrier, barrier_ids)

    @timing
    def get_similar_barriers(
        self, barrier: BarrierEntry, similarity_threshold: float, quantity: int
    ):
        barrier_ids = self.get_barrier_ids()

        if barrier.id not in barrier_ids:
            self.add_barrier(barrier, barrier_ids)

        cosine_sim = self.get_cosine_sim()

        index = None
        for i, barrier_id in enumerate(barrier_ids):
            if barrier_id == barrier.id:
                index = i
                break

        scores = cosine_sim[index]
        barrier_scores = dict(zip(barrier_ids, scores))
        barrier_scores = {
            k: v
            for k, v in barrier_scores.items()
            if v > similarity_threshold and k != barrier.id
        }
        barrier_scores = sorted(barrier_scores.items(), key=lambda x: x[1])[-quantity:]

        barrier_ids = [b[0] for b in barrier_scores]
        return barrier_ids


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
        return

    data = get_data()  # List[Dict]
    manager = RelatedBarrierManager(data)


def barrier_to_corpus(barrier):
    return barrier.title + ". " + barrier.summary
