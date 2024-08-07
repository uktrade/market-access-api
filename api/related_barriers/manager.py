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
import torch

from api.barriers.tasks import get_barriers_overseas_region
from api.interactions.models import Interaction
from api.related_barriers.constants import BarrierEntry

from api.metadata.utils import (get_sector)

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

    def __init__(self):
        """
        Only called once in a execution lifecycle
        """
        self.__transformer = get_transformer()

    @timing
    def set_data(self, data: List[Dict]):
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
    def flush():
        logger.info("(Related Barriers): flush cache")
        cache.delete(EMBEDDINGS_CACHE_KEY)
        cache.delete(BARRIER_IDS_CACHE_KEY)

    @staticmethod
    def set_embeddings(embeddings):
        logger.info("(Related Barriers): set_embeddings")
        cache.set(EMBEDDINGS_CACHE_KEY, embeddings, timeout=None)

    @staticmethod
    def set_barrier_ids(barrier_ids):
        logger.info("(Related Barriers): barrier_ids")
        cache.set(BARRIER_IDS_CACHE_KEY, barrier_ids, timeout=None)

    @staticmethod
    def get_embeddings():
        logger.info("(Related Barriers): get_embeddings")
        return cache.get(EMBEDDINGS_CACHE_KEY, [])

    @staticmethod
    def get_barrier_ids():
        logger.info("(Related Barriers): get_barrier_ids")
        return cache.get(BARRIER_IDS_CACHE_KEY, [])

    @property
    def model(self):
        return self.__transformer

    @timing
    def get_cosine_sim(self):
        logger.info("(Related Barriers): get_cosine_sim")
        embeddings = self.get_embeddings()
        return util.cos_sim(embeddings, embeddings)

    @timing
    def encode_barrier_corpus(self, barrier: BarrierEntry):
        return self.model.encode(barrier.barrier_corpus, convert_to_tensor=True).numpy()

    @timing
    def add_barrier(
        self, barrier: BarrierEntry, barrier_ids: Optional[List[str]] = None
    ):
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
    def remove_barrier(self, barrier: BarrierEntry, barrier_ids=None):
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
    def update_barrier(self, barrier: BarrierEntry):
        logger.info(f"(Related Barriers): update_barrier {barrier.id}")
        barrier_ids = manager.get_barrier_ids()
        if barrier.id in barrier_ids:
            self.remove_barrier(barrier, barrier_ids)
        self.add_barrier(barrier, barrier_ids)

    @timing
    def get_similar_barriers(
        self, barrier: BarrierEntry, similarity_threshold: float, quantity: int
    ):
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
        barrier_scores = sorted(barrier_scores.items(), key=lambda x: x[1])[-quantity:]

        barrier_ids = [b[0] for b in barrier_scores]
        return barrier_ids
    

    @timing
    def get_similar_barriers_searched(
        self, search_term: str, similarity_threshold: float, quantity: int, log_score: bool,
    ):

        logger.info(f"(Related Barriers): get_similar_barriers_seaarched")
        barrier_ids = self.get_barrier_ids()

        # RESTORE THESE 2 LINES BEFORE COMMITTING - CACHING NEEDS TO GO FOR TESTING PURPOSESES
        #if not barrier_ids:
        #    self.set_data(get_data())
        # DELETE THIS LINE BEFORE COMMITTING - CACHING SHOULD COME BACK FOR REAL
        self.set_data(get_data())

        barrier_ids = self.get_barrier_ids()

        embedded_index = "search_term"
        search_term_embedding = self.model.encode(search_term, convert_to_tensor=True).numpy()
        embeddings = self.get_embeddings()
        new_embeddings = numpy.vstack([embeddings, search_term_embedding])  # append embedding
        new_barrier_ids = barrier_ids + [embedded_index]  # append barrier_id

        cosine_sim = util.cos_sim(new_embeddings, new_embeddings)



        #embedder = SentenceTransformer("paraphrase-MiniLM-L3-v2")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        corpo_list = []
        for thing in get_data():
            corpo_list.append(thing["barrier_corpus"])
        logger.critical("_________")
        logger.critical(corpo_list)
        logger.critical("_________")
        corpus_embeddings = embedder.encode(corpo_list, convert_to_tensor=True)
        top_k = min(5, 50)
        query_embedding = embedder.encode(search_term, convert_to_tensor=True)
        similarity_scores = embedder.similarity(query_embedding, corpus_embeddings)[0]
        scores_2, indices = torch.topk(similarity_scores, k=top_k)
        logger.critical("++++++++++++++++++++++++++++++++++++++")
        logger.critical("++++++++++++++++++++++++++++++++++++++")
        for score, idx in zip(scores_2, indices):
            print(corpo_list[idx], "(Score: {:.4f})".format(score))
        logger.critical("++++++++++++++++++++++++++++++++++++++")
        logger.critical("++++++++++++++++++++++++++++++++++++++")









        index = len(embeddings)

        scores = cosine_sim[index]
        barrier_scores = dict(zip(new_barrier_ids, scores))

        barrier_scores = {
            k: v
            for k, v in barrier_scores.items()
            if v > similarity_threshold
        }


        logger.critical(barrier_scores.items())
        logger.critical("-")

        barrier_scores = sorted(barrier_scores.items(), key=lambda x: x[1])#[-quantity:]

        if log_score:
            logger.critical(barrier_scores)
            
        barrier_ids = [b[0] for b in barrier_scores]
        return barrier_ids


manager: Optional[RelatedBarrierManager] = None


def get_data() -> List[Dict]:
    from api.barriers.models import Barrier

    # ./manage.py run_test

    data_dictionary = []
    barriers = Barrier.objects.filter(archived=False).exclude(draft=True)
    for barrier in barriers:
        corpus_object = {}

        # Companies tests - 
        # 
        # "Barriers that affect barclays bank"
        # WITH Additional sentence text
        #('dde42f8f-b02b-41a6-b794-3cb6e1cdade5', tensor(0.3390))
        # WITHOUT Additional sentence text
        #('dde42f8f-b02b-41a6-b794-3cb6e1cdade5', tensor(0.2761))
        # (Barrier with Barclays PLC not the highest match)
        #
        # "Barclays bank"
        # No results - one word match results in too low a threshold for result
        #
        # "show me barriers that are related to Barclays bank"
        # WITH Additional sentence text
        # ('dde42f8f-b02b-41a6-b794-3cb6e1cdade5', tensor(0.4561))
        # barrier with Barlays under companies comes 2nd in matching - the highest
        # has a export description of "Deal account account tough" - which could be words
        # related to the query word "bank"
        # WITHOUT Additional sentence text
        # Expected barrier did not appear

        companies_affected_list = ""
        if barrier.companies:
            for company in barrier.companies:
                company_affected_corpus = (
                    "Company called " + company["name"] + " is affected by this barrier. "
                )
                companies_affected_list = companies_affected_list + company_affected_corpus
                #companies_affected_list = companies_affected_list + str(company) + " "

        other_organisations_affected_list = ""
        if barrier.related_organisations:
            for company in barrier.related_organisations:
                other_organisations_affected_corpus = (
                    "Company called " + company["name"] + " is affected by this barrier. "
                )
                other_organisations_affected_list = other_organisations_affected_list + other_organisations_affected_corpus
                #other_organisations_affected_list = other_organisations_affected_list + str(company) + " "

        # Notes Tests - 
        #
        # "Barriers that need Santino Molinaros attention"
        notes_text_list = ""
        for note in barrier.interactions_documents.all():
            notes_text_list = notes_text_list + note.text + " "


        # Sectors Tests - 
        #
        # "Barriers that are affecting the maritime sector"
        sectors_list = [get_sector(str(sector_id))["name"] for sector_id in barrier.sectors]
        sectors_list.append(get_sector(barrier.main_sector)["name"])
        sectors_text = ""
        if len(sectors_list) > 0:
            for sector_name in sectors_list:
                sectors_text = sectors_text + f" Affects the {sector_name} sector. Related to the {sector_name} sector."

        # Overseas Region Tests -
        #
        # "Barriers owned by the South Asia region team"
        #
        # "Barriers affecting South Asia region"

        overseas_region_name = get_barriers_overseas_region(barrier.country, barrier.trading_bloc)
        overseas_region_text = f"Belongs to the {overseas_region_name} regional team. Affects the {overseas_region_name} region. Owned by the {overseas_region_name} regional team"
        #overseas_region_text = f"{overseas_region_name}"

        # ERD tests - 
        #
        # "Barriers which are estimated to be resolved on 23 June 2024"
        # Expected result not returned, but did get results back
        #
        # "barrier is estimated to be resolved on 23 June 2024"
        # Expected result not returned, but did get results back

        estimated_resolution_date_text = ""
        date_formats = [
	        "%d-%m-%Y",
            "%d/%m/%Y",
            "%d %m %Y",
	        "%d-%m-%y",
            "%d/%m/%y",
            "%d %m %y",
            "%d %b %Y",
            "%d %B %Y",
            "%x",
            "%M %y",
            "%M %Y",
            "%M %d %y",
            "%M %d %Y"
        ]
        if barrier.estimated_resolution_date:
            for date_format in date_formats:
                formatted_date = barrier.estimated_resolution_date.strftime(date_format)
                #if formatted_date == "23 June 2024":
                #    logger.critical("======================")
                #    logger.critical(barrier.id)
                #    logger.critical("======================")
                estimated_resolution_date_text = estimated_resolution_date_text + f"Estimated to be resolved on {formatted_date}. "
            #estimated_resolution_date_text = str(barrier.estimated_resolution_date)

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

        logger.critical("-")
        logger.critical(corpus_object["barrier_corpus"])
        logger.critical("-")

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


def barrier_to_corpus(barrier):
    return barrier.title + ". " + barrier.summary
