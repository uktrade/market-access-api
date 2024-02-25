import logging
import time
from functools import wraps
from typing import Dict, List, Optional

import numpy
import pandas
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


class RelatedBarrierModelWarehouse:
    __model: Optional[SentenceTransformer] = None

    def __init__(self, data: List[Dict]):
        self.__model = load_transformer()

        @timing
        def set_data():
            barrier_ids = [str(d["id"]) for d in data]
            barrier_data = [d["barrier_corpus"] for d in data]
            embeddings = self.__model.encode(barrier_data, convert_to_tensor=True)

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
        return self.__model

    @timing
    def get_cosine_sim(self):
        embeddings = self.get_embeddings()
        barrier_ids = self.get_barrier_ids()
        return pandas.DataFrame(
            util.cos_sim(embeddings, embeddings),
            index=barrier_ids,
            columns=barrier_ids,
        )

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
        if barrier["id"] in db.get_barrier_ids():
            self.remove_barrier(barrier)
        self.add_barrier(barrier)


db: Optional[RelatedBarrierModelWarehouse] = None


def set_db(database: RelatedBarrierModelWarehouse):
    global db

    if db:
        raise Exception("DB already set, please stop db or restart application")

    db = database


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


def create_db() -> RelatedBarrierModelWarehouse:
    data = get_data()  # List[Dict]

    return RelatedBarrierModelWarehouse(data)


@timing
def get_similar_barriers(barrier: Dict):
    if not db:
        raise Exception("Related Barrier DB not set")

    if barrier["id"] not in db.get_barrier_ids():
        db.add_barrier(barrier)

    # db.update_barrier(barrier)

    df = db.get_cosine_sim()

    scores = (
        df[barrier["id"]]
        .sort_values(ascending=False)[:SIMILAR_BARRIERS_LIMIT]
        .drop(barrier["id"])
    )
    barrier_ids = scores[scores > SIMILARITY_THRESHOLD].index

    return barrier_ids


def barrier_to_corpus(barrier):
    return barrier.title + ". " + barrier.summary
