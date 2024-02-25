import json
import os

import numpy as np
import pandas as pd
from django.conf import settings
from django.core.cache import cache
from django.db.models import CharField, QuerySet
from django.db.models import Value as V
from django.db.models.functions import Concat
from sentence_transformers import SentenceTransformer, util
from typing_extensions import Self

from api.barriers.models import Barrier

SIMILARITY_THRESHOLD = 0.19
SIMILAR_BARRIERS_LIMIT = 5

# https://www.sbert.net/docs/pretrained_models.html
# Load the sentence transformer model
# albert-small-v2 # 43 MB size
# smaller model
transformer_model = SentenceTransformer("paraphrase-MiniLM-L3-v2")

RELEVANT_BARRIER_FIELDS = [
    "title",
    "summary",
]


class SimilarityScoreMatrix(pd.DataFrame):
    similarity_score_df_path = os.path.join(
        settings.ROOT_DIR, "barrier_similarity_scores_df.json"
    )

    @property
    def base_class_view(self):
        # use this to view the base class, needed for debugging in some IDEs.
        return pd.DataFrame(self)

    @property
    def _constructor(self):
        return SimilarityScoreMatrix

    @staticmethod
    def get_annotated_barrier_queryset(barrier_ids: list = None):
        if barrier_ids:
            starting_queryset = Barrier.objects.filter(id__in=barrier_ids)
        else:
            starting_queryset = Barrier.objects.all()

        annotated_queryset = (
            starting_queryset.exclude(draft=True)
            .annotate(
                barrier_corpus=Concat(
                    "title", V(". "), "summary", output_field=CharField()
                )
            )
            .values("id", "barrier_corpus")
        )
        if barrier_ids:
            annotated_queryset = annotated_queryset.filter(id__in=barrier_ids)
        return annotated_queryset

    @classmethod
    def create_matrix(cls) -> Self:
        """Create a similarity scores matrix for all barriers.

        The similarity scores matrix is a square matrix where the rows and columns are barrier ids. And the values
        at each intersection is the similarity score between the two barriers.

        The similarity score matrix is then saved to a json file and cached."""
        barriers = cls.get_annotated_barrier_queryset()
        barrier_ids = [str(barrier["id"]) for barrier in barriers]
        barrier_corpuses = [barrier["barrier_corpus"] for barrier in barriers]
        barrier_embeddings = transformer_model.encode(
            barrier_corpuses, convert_to_tensor=True
        )
        cosine_scores = util.cos_sim(barrier_embeddings, barrier_embeddings)
        new_matrix = cls(
            cosine_scores.numpy(),
            index=barrier_ids,
            columns=barrier_ids,
        )

        return new_matrix.save_matrix()  # saving to JSON and caching

    @classmethod
    def retrieve_matrix(cls) -> Self:
        """Retrieve the similarity scores matrix from the cache or from the json file if it exists."""
        if similarity_score_json := cache.get(
            settings.BARRIER_SIMILARITY_MATRIX_CACHE_KEY
        ):
            return cls(pd.read_json(similarity_score_json))  # retrieving from cache
        else:
            if os.path.isfile(cls.similarity_score_df_path):
                with open(cls.similarity_score_df_path, "r") as f:
                    dataframe_json = json.load(f)
                    cache.set(  # caching the matrix, so it can be retrieved from the cache next time
                        settings.BARRIER_SIMILARITY_MATRIX_CACHE_KEY,
                        dataframe_json,
                        timeout=None,
                    )
                    return cls(pd.read_json(dataframe_json))
            else:
                return cls.create_matrix()  # creating the matrix if it doesn't exist

    def update_matrix(self, barrier_object) -> Self:
        """Given a barrier, update the similarity scores matrix column for that barrier.

        Similarity scores are computed using cosine similarity between the barrier embeddings."""
        barrier_id = str(barrier_object.id)

        if barrier_id not in self.columns:
            return self.add_barrier(barrier_object)

        barrier_ids = self.index.tolist()
        annotated_barrier_queryset = self.get_annotated_barrier_queryset(barrier_ids)
        barrier_corpuses = [
            barrier["barrier_corpus"] for barrier in annotated_barrier_queryset
        ]
        barrier_embeddings = transformer_model.encode(
            barrier_corpuses, convert_to_tensor=True
        )
        this_barrier_embedding = annotated_barrier_queryset.get(id=barrier_id)[
            "barrier_corpus"
        ]
        similarity_scores = util.cos_sim(this_barrier_embedding, barrier_embeddings)
        self[barrier_id] = similarity_scores.numpy()[0]

        return self.save_matrix()

    def save_matrix(self) -> Self:
        """Save the similarity scores matrix to a JSON file and caching it."""

        # converting to string for JSON serialisation
        dataframe_json = self.to_json(default_handler=str)
        cache.set(
            settings.BARRIER_SIMILARITY_MATRIX_CACHE_KEY, dataframe_json, timeout=None
        )
        with open(self.similarity_score_df_path, "w") as f:
            json.dump(dataframe_json, f)

        return self

    def add_barrier(self, barrier_object) -> Self:
        """Add a barrier to the similarity scores matrix.

        This is made a little difficult by Pandas, so we create a new matrix with the new barrier and then return that
        instead."""
        barrier_id = str(barrier_object.id)

        self[barrier_id] = np.nan  # creating the empty column
        new_row = {}
        for barrier in self:
            new_row[barrier] = np.nan
        new_row = pd.Series(new_row, name=barrier_id)

        new_matrix = pd.concat([self, pd.DataFrame([new_row], columns=new_row.index)])
        return new_matrix.update_matrix(barrier_object)

    def retrieve_similar_barriers(
        self,
        barrier_object,
        limit=SIMILAR_BARRIERS_LIMIT,
        threshold=SIMILARITY_THRESHOLD,
    ) -> QuerySet:
        """Retrieve similar barriers for a given barrier object."""
        barrier_id = str(barrier_object.id)

        if barrier_id not in self.columns:
            new_matrix = self.add_barrier(barrier_object)
            return new_matrix.retrieve_similar_barriers(
                barrier_object, limit, threshold
            )

        barrier_similarity_scores = (
            self[barrier_id].sort_values(ascending=False)[:limit].drop(barrier_id)
        )
        barrier_similarity_scores = barrier_similarity_scores[
            barrier_similarity_scores > threshold
        ]
        barrier_queryset = Barrier.objects.filter(
            id__in=barrier_similarity_scores.index
        )
        return barrier_queryset
