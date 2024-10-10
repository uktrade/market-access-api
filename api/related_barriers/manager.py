import logging
import time
from functools import wraps
from typing import Dict, List, Optional

import numpy
import torch
from django.core.cache import cache
from sentence_transformers import SentenceTransformer, util

from api.barriers.tasks import get_barriers_overseas_region
from api.metadata.utils import get_sector
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
    return SentenceTransformer("all-MiniLM-L6-v2")


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

    def __str__(self) -> str:
        return "Related Barrier Manager"

    def __init__(self) -> None:
        """
        Only called once in a execution lifecycle
        """
        self.__transformer = get_transformer()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

    @timing
    def set_data(self, data: List[Dict]) -> None:
        """
        Load data into memory.
        """
        logger.info("(Related Barriers): set_data")
        self.flush()
        barrier_ids = [str(d["id"]) for d in data]
        barrier_data = [d["barrier_corpus"] for d in data]
        embeddings = self.__transformer.encode(barrier_data, convert_to_tensor=True)
        self.set_embeddings(embeddings.numpy())
        self.set_barrier_ids(barrier_ids)

    @staticmethod
    def flush() -> None:
        logger.info("(Related Barriers): flush cache")
        cache.delete(EMBEDDINGS_CACHE_KEY)
        cache.delete(BARRIER_IDS_CACHE_KEY)

    @staticmethod
    def set_embeddings(embeddings) -> None:
        logger.info("(Related Barriers): set_embeddings")
        cache.set(EMBEDDINGS_CACHE_KEY, embeddings, timeout=None)

    @staticmethod
    def set_barrier_ids(barrier_ids) -> None:
        logger.info("(Related Barriers): barrier_ids")
        cache.set(BARRIER_IDS_CACHE_KEY, barrier_ids, timeout=None)

    @staticmethod
    def get_embeddings() -> numpy.ndarray:
        logger.info("(Related Barriers): get_embeddings")
        return cache.get(EMBEDDINGS_CACHE_KEY, [])

    @staticmethod
    def get_barrier_ids() -> List[str]:
        logger.info("(Related Barriers): get_barrier_ids")
        return cache.get(BARRIER_IDS_CACHE_KEY, [])

    @property
    def model(self) -> SentenceTransformer:
        return self.__transformer

    @timing
    def get_cosine_sim(self) -> numpy.ndarray:
        logger.info("(Related Barriers): get_cosine_sim")
        embeddings = self.get_embeddings()
        return util.cos_sim(embeddings, embeddings)

    @timing
    def encode_barrier_corpus(self, barrier: BarrierEntry) -> numpy.ndarray:
        return self.model.encode(barrier.barrier_corpus, convert_to_tensor=True).numpy()

    @timing
    def add_barrier(
        self, barrier: BarrierEntry, barrier_ids: Optional[List[str]] = None
    ) -> None:
        logger.info(f"(Related Barriers): add_barrier {barrier.id}")
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
    def remove_barrier(self, barrier: BarrierEntry, barrier_ids=None) -> None:
        logger.info(f"(Related Barriers): remove_barrier {barrier.id}")
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
    def update_barrier(self, barrier: BarrierEntry) -> None:
        logger.info(f"(Related Barriers): update_barrier {barrier.id}")
        barrier_ids = self.get_barrier_ids()
        if barrier.id in barrier_ids:
            self.remove_barrier(barrier, barrier_ids)
        self.add_barrier(barrier, barrier_ids)

    @timing
    def get_similar_barriers(
        self, barrier: BarrierEntry, similarity_threshold: float, quantity: int
    ) -> List[tuple]:
        logger.info(f"(Related Barriers): get_similar_barriers {barrier.id}")
        barrier_ids = self.get_barrier_ids()

        if not barrier_ids:
            self.set_data(get_data())

        barrier_ids = self.get_barrier_ids()

        if barrier.id not in barrier_ids:
            self.add_barrier(barrier, barrier_ids)

        barrier_ids = self.get_barrier_ids()
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
        results = sorted(barrier_scores.items(), key=lambda x: x[1])[-quantity:]
        return [(r[0], torch.round(torch.tensor(r[1]), decimals=4)) for r in results]

    @timing
    def get_similar_barriers_searched(
        self, search_term: str, similarity_threshold: float, quantity: int = None
    ) -> Optional[List[tuple]]:
        """
        Search for similar barriers based on a search term.

        :param search_term: The search term to compare against the barrier corpus
        :param similarity_threshold: The threshold for the cosine similarity score
        :param quantity: The number of similar barriers to return

        :returns: A list of similar barriers or None

        The None is returned if no barrier ids are found in the cache.
        which is a sign that the cache has been flushed.
        """

        logger.info("(Related Barriers): get_similar_barriers_searched")

        if not (barrier_ids := self.get_barrier_ids()):
            self.set_data(get_data())
            barrier_ids = self.get_barrier_ids() or []

        if not barrier_ids:
            logger.warning("(Related Barriers): No barrier ids found")
            return

        embedded_index = "search_term"
        search_term_embedding = self.model.encode(
            search_term, convert_to_tensor=True
        ).numpy()
        embeddings = self.get_embeddings()
        new_embeddings = numpy.vstack(
            [embeddings, search_term_embedding]
        )  # append embedding
        new_barrier_ids = barrier_ids + [embedded_index]  # append barrier_id

        cosine_sim = util.cos_sim(new_embeddings, new_embeddings)

        index_search_term_embedding = len(new_embeddings) - 1
        scores = cosine_sim[index_search_term_embedding]
        barrier_scores = dict(zip(new_barrier_ids, scores))
        barrier_scores = {
            k: v
            for k, v in barrier_scores.items()
            if v > similarity_threshold and k != embedded_index
        }
        results = sorted(barrier_scores.items(), key=lambda x: x[1])[-quantity:]
        return [(r[0], torch.round(r[1], decimals=4)) for r in results]


def get_data() -> List[Dict]:
    from api.barriers.models import Barrier

    data_dictionary = []
    barriers = (
        Barrier.objects.prefetch_related("interactions_documents")
        .filter(archived=False)
        .exclude(draft=True)
    )
    for barrier in barriers:
        data_dictionary.append(
            {"id": str(barrier.id), "barrier_corpus": barrier_to_corpus(barrier)}
        )

    return data_dictionary


def get_or_init() -> RelatedBarrierManager:
    manager = RelatedBarrierManager()

    if not manager.get_barrier_ids():
        logger.info("(Related Barriers): Initialising)")
        data = get_data()
        manager.set_data(data)

    return manager


def barrier_to_corpus(barrier) -> str:
    companies_affected_list = ""
    if barrier.companies:
        companies_affected_list = ", ".join(
            [company["name"] for company in barrier.companies]
        )

    other_organisations_affected_list = ""
    if barrier.related_organisations:
        other_organisations_affected_list = ", ".join(
            [company["name"] for company in barrier.related_organisations]
        )

    notes_text_list = ", ".join(
        [note.text for note in barrier.interactions_documents.all()]
    )

    sectors_list = [
        get_sector(str(sector_id))["name"]
        for sector_id in barrier.sectors
        if get_sector(str(sector_id))
    ]
    main_sector = get_sector(barrier.main_sector)
    if main_sector:
        sectors_list.append(main_sector["name"])
    sectors_text = ", ".join(sectors_list)

    overseas_region_text = get_barriers_overseas_region(
        barrier.country, barrier.trading_bloc
    )

    estimated_resolution_date_text = ""
    if barrier.estimated_resolution_date:
        date = barrier.estimated_resolution_date.strftime("%d-%m-%Y")
        estimated_resolution_date_text = f"Estimated to be resolved on {date}."

    return (
        f"{barrier.title}. {barrier.summary}. "
        f"{sectors_text} {barrier.country_name}. "
        f"{overseas_region_text}. {companies_affected_list} "
        f"{other_organisations_affected_list} {notes_text_list}. "
        f"{barrier.status_summary}. {estimated_resolution_date_text}. "
        f"{barrier.export_description}."
    )
