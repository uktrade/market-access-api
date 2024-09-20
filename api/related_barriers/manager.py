import logging
import time
from functools import wraps
from typing import Dict, List, Optional

import numpy
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
    # SentenceTransformer("all-MiniLM-L6-v2")
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
        barrier_ids = manager.get_barrier_ids()
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
        return sorted(barrier_scores.items(), key=lambda x: x[1])[-quantity:]

    # HOW TO TEST:

    # 1. Have market-access-api container running
    # 2. exec into contatiner
    # 3. ./manage.py shell_plus
    # 4. copy and paste imports:
    #
    #    from api.related_barriers import manager as handler_manager
    #    from api.related_barriers.constants import (
    #        SIMILAR_BARRIERS_LIMIT,
    #        SIMILARITY_THRESHOLD,
    #    )
    #
    # 5. Set your search term:
    #
    #   value="<SEARCH_TERM GOES HERE"
    #
    # 6. To run against existing cosine and model:
    #
    #    if handler_manager.manager is None:
    #        handler_manager.init()
    #    barrier_scores = handler_manager.manager.get_similar_barriers_searched(
    #        search_term=value,
    #        similarity_threshold=SIMILARITY_THRESHOLD,
    #        quantity=SIMILAR_BARRIERS_LIMIT,
    #    )
    #
    # 7. To run against similarity method and "all" model:
    #
    #    if handler_manager.manager is None:
    #        handler_manager.init()
    #    barrier_scores = handler_manager.manager.get_semantic_search(
    #        search_term=value,
    #        similarity_threshold=SIMILARITY_THRESHOLD,
    #        quantity=SIMILAR_BARRIERS_LIMIT,
    #    )

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
            self.set_data(get_data_semantic_search())
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

        # RESTORE THIS FOR REAL VERSION:
        # barrier_scores = {
        #    k: v
        #    for k, v in barrier_scores.items()
        #    if v > similarity_threshold and k != embedded_index
        # }

        RESULT = sorted(barrier_scores.items(), key=lambda x: x[1])[-6:]

        logger.critical("+++++++++++++++++++ BARRIER SCORES")
        for item in RESULT:
            if str(item[0]) != "search_term":
                logger.critical(str(item[0]) + " - " + str(item[1]))
                logger.critical("-")
        logger.critical("+++++++++++++++++++ BARRIER SCORES")

        return sorted(barrier_scores.items(), key=lambda x: x[1])[-quantity:]

    @timing
    def get_semantic_search(
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

        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        # change to this to use existing mini model
        # embedder = get_transformer()

        # "get_data_semantic_seach" - original/current string matcher
        # "get_data_semantic_search_sentence_structured" - method with added sentence structure around corpus values
        if not (barrier_ids := self.get_barrier_ids()):
            self.set_data(get_data_semantic_search())
            barrier_ids = self.get_barrier_ids() or []

        if not barrier_ids:
            logger.warning("(Related Barriers): No barrier ids found")
            return

        embedded_index = "search_term"
        search_term_embedding = self.model.encode(
            search_term, convert_to_tensor=True
        ).numpy()

        embeddings = self.get_embeddings()
        scores = embedder.similarity(search_term_embedding, embeddings)
        barrier_scores = dict(zip(barrier_ids, scores[0]))

        # RESTORE THIS FOR REAL VERSION:
        # barrier_scores = {
        #    k: v
        #    for k, v in barrier_scores.items()
        #    if v > similarity_threshold
        # }

        RESULT = sorted(barrier_scores.items(), key=lambda x: x[1])[-5:]

        logger.critical("+++++++++++++++++++ BARRIER SCORES")
        for item in RESULT:
            if str(item[0]) != "search_term":
                logger.critical(str(item[0]) + " - " + str(item[1]))
                logger.critical("-")
        logger.critical("+++++++++++++++++++ BARRIER SCORES")

        return sorted(barrier_scores.items(), key=lambda x: x[1])[-quantity:]


manager: Optional[RelatedBarrierManager] = None


def get_data() -> List[Dict]:
    from api.barriers.models import Barrier

    return [
        {"id": barrier.id, "barrier_corpus": f"{barrier.title} . {barrier.summary}"}
        for barrier in Barrier.objects.filter(archived=False).exclude(draft=True)
    ]


def get_data_semantic_search() -> List[Dict]:
    from api.barriers.models import Barrier

    data_dictionary = []
    barriers = Barrier.objects.filter(archived=False).exclude(draft=True)
    for barrier in barriers:
        corpus_object = {}

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
            get_sector(str(sector_id))["name"] for sector_id in barrier.sectors
        ]
        sectors_list.append(get_sector(barrier.main_sector)["name"])
        sectors_text = ", ".join(sectors_list)

        overseas_region_text = get_barriers_overseas_region(
            barrier.country, barrier.trading_bloc
        )

        estimated_resolution_date_text = ""
        if barrier.estimated_resolution_date:
            date = barrier.estimated_resolution_date.strftime("%d-%m-%Y")
            estimated_resolution_date_text = f"Estimated to be resolved on {date}."

        corpus_object["id"] = barrier.id
        corpus_object["barrier_corpus"] = (
            f"{barrier.title}. "
            f"{barrier.summary}. "
            f"{sectors_text} "
            f"{barrier.country_name}. "
            f"{overseas_region_text}. "
            f"{companies_affected_list} "
            f"{other_organisations_affected_list} "
            f"{notes_text_list}. "
            f"{barrier.status_summary}. "
            f"{estimated_resolution_date_text}. "
            f"{barrier.export_description}."
        )

        data_dictionary.append(corpus_object)

    return data_dictionary


def get_data_semantic_search_sentence_structured() -> List[Dict]:
    from api.barriers.models import Barrier

    data_dictionary = []
    barriers = Barrier.objects.filter(archived=False).exclude(draft=True)
    for barrier in barriers:
        corpus_object = {}

        companies_affected_list = ""
        if barrier.companies:
            companies_affected_list = ", ".join(
                [company["name"] for company in barrier.companies]
            )
        companies_affected_list = (
            "The following companies are affected; " + companies_affected_list
        )

        other_organisations_affected_list = ""
        if barrier.related_organisations:
            other_organisations_affected_list = ", ".join(
                [company["name"] for company in barrier.related_organisations]
            )
        other_organisations_affected_list = (
            "The following organisations are affected; "
            + other_organisations_affected_list
        )

        notes_text_list = ", ".join(
            [note.text for note in barrier.interactions_documents.all()]
        )

        sectors_list = [
            get_sector(str(sector_id))["name"] for sector_id in barrier.sectors
        ]
        sectors_list.append(get_sector(barrier.main_sector)["name"])
        sectors_text = ", ".join(sectors_list)
        sectors_list = "The following sectors are affected; " + sectors_list

        overseas_region_text = get_barriers_overseas_region(
            barrier.country, barrier.trading_bloc
        )
        overseas_region_text = (
            "The following regions and countries are affected; " + overseas_region_text
        )

        estimated_resolution_date_text = ""
        if barrier.estimated_resolution_date:
            date = barrier.estimated_resolution_date.strftime("%d-%m-%Y")
            estimated_resolution_date_text = f"Estimated to be resolved on {date}."

        corpus_object["id"] = barrier.id
        corpus_object["barrier_corpus"] = (
            f"{barrier.title}. "
            f"{barrier.summary}. "
            f"{sectors_text} "
            f"{barrier.country_name}. "
            f"{overseas_region_text}. "
            f"{companies_affected_list} "
            f"{other_organisations_affected_list} "
            f"{notes_text_list}. "
            f"{barrier.status_summary}. "
            f"{estimated_resolution_date_text}. "
            f"{barrier.export_description}."
        )

        data_dictionary.append(corpus_object)

    return data_dictionary


def init():
    global manager

    if manager:
        raise Exception("Related Barrier Manager already set")

    manager = RelatedBarrierManager()

    if not manager.get_barrier_ids():
        logger.info("(Related Barriers): Initialising)")
        data = get_data()
        manager.set_data(data)


def barrier_to_corpus(barrier) -> str:
    return barrier.title + ". " + barrier.summary
