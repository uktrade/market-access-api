from typing import List, Dict, Optional

from django.db.models import CharField
from django.db.models import Value as V
from django.db.models.functions import Concat
from sentence_transformers import SentenceTransformer, util


class RelatedBarrierModelWarehouse:
    __model: Optional[SentenceTransformer] = None
    __embeddings = None
    __cosine_sim = None
    __redis = None

    def __init__(self, data: List[Dict]):
        model = SentenceTransformer("paraphrase-MiniLM-L3-v2")
        embeddings = self.__model.model.encode(
            [d["barrier_corpus"] for d in data], convert_to_tensor=True
        )
        cosine_sim = util.cos_sim(embeddings, embeddings)

        self.__model = model
        self.__embeddings = embeddings
        self.__cosine_sim = cosine_sim
        self.__redis = None

    def get_model(self):
        return self.__model

    def get_embeddings(self):
        if self.__redis:
            pass
        return self.__model

    def get_cosine_sim(self):
        if self.__redis:
            pass
        return self.__model

    def update_model(self):
        # Queued to avoid race conditions
        # The truth is only the latest update, so if an update is already running,
        # we don't need to schedule a new job. this way if 100 requests come in,
        # the task knows it will rerun
        #
        # O(T) = max(0, T(update_model()))
        # Check if a task exist
        if self.__redis:
            if self.__redis.get_waiting_task_count('update_model'):
                # Task is already waiting to be run that includes this timestamp
                return

        pass


db: Optional[RelatedBarrierModelWarehouse] = None


def set_db(database: RelatedBarrierModelWarehouse):
    global db

    if db:
        raise Exception('DB already set, please stop db or restart application')

    db = database


def get_data() -> List[Dict]:
    from api.barriers.models import Barrier

    return (
        Barrier.objects.filter(archived=False).exclude(draft=True)
        .annotate(
            barrier_corpus=Concat(
                "title", V(". "), "summary", output_field=CharField()
            )
        )
        .values("id", "barrier_corpus")
    )


def create_db() -> RelatedBarrierModelWarehouse:
    data = get_data()  # List[Dict]

    return RelatedBarrierModelWarehouse(data)

