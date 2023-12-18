import json
import os
from collections import UserDict

import numpy as np
import pandas as pd
import torch
from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.barrier_embeddings_dict = BarrierEmbeddingDict()

    @property
    def _constructor(self):
        return SimilarityScoreMatrix

    @classmethod
    def create_matrix(cls) -> Self:
        """Create a similarity scores matrix for all barriers.

        The similarity scores matrix is a square matrix where the rows and columns are barrier ids. And the values
        at each intersection is the similarity score between the two barriers.

        The similarity score matrix is then saved to a json file and cached."""
        barriers = Barrier.objects.exclude(draft=True)
        barrier_ids = [str(barrier.id) for barrier in barriers]
        new_matrix = cls(index=barrier_ids, columns=barrier_ids)  # creating empty df

        for (
            current_barrier_id,
            embeddings_dict,
        ) in new_matrix.barrier_embeddings_dict.items():
            # looping through the barrier embeddings, and
            # computing the similarity scores between each and saving to the matrix
            barrier_embedding = new_matrix.barrier_embeddings_dict[current_barrier_id]
            similarity_scores_matrix_column = new_matrix.loc[current_barrier_id]
            for (
                relevant_barrier_id,
                relevant_barrier_similarity_score,
            ) in similarity_scores_matrix_column.items():
                if relevant_barrier_id == current_barrier_id:
                    continue
                similarity_score = util.cos_sim(
                    barrier_embedding,
                    new_matrix.barrier_embeddings_dict[relevant_barrier_id],
                )
                # converting to float for easy JSON serialisation
                float_similarity_score = similarity_score.item()

                # saving to the matrix
                new_matrix[current_barrier_id][
                    relevant_barrier_id
                ] = float_similarity_score

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
        """Given a barrier id, update the similarity scores matrix column for that barrier.

        Similarity scores are computed using cosine similarity between the barrier embeddings."""
        barrier_id = str(barrier_object.id)
        if barrier_id not in self.columns:
            return self.add_barrier(barrier_object)

        barrier_embedding = self.compute_barrier_embedding(barrier_object)
        similarity_scores_matrix_column = self.loc[barrier_id]

        for (
            relevant_barrier_id,
            relevant_barrier_similarity_score,
        ) in similarity_scores_matrix_column.items():
            if relevant_barrier_id == barrier_id:
                continue

            similarity_score = util.cos_sim(
                barrier_embedding,
                self.barrier_embeddings_dict[relevant_barrier_id],
            )
            # converting to float for easy JSON serialisation
            float_similarity_score = similarity_score.item()

            self[barrier_id][relevant_barrier_id] = float_similarity_score

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

        self.barrier_embeddings_dict.save_dict()

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

    @staticmethod
    def compute_barrier_embedding(barrier_object):
        """Compute the embedding for a barrier."""
        barrier_corpus = SimilarityScoreMatrix.get_barrier_corpus(barrier_object)
        return transformer_model.encode(barrier_corpus, convert_to_tensor=True)

    @staticmethod
    def get_barrier_corpus(barrier_object) -> str:
        """Get the corpus for a barrier.

        This is a concatenation of relevant fields, like summary and title."""
        barrier_corpus = ""
        for index, field in enumerate(RELEVANT_BARRIER_FIELDS):
            barrier_corpus += getattr(barrier_object, field)
            if index == len(RELEVANT_BARRIER_FIELDS) - 1:
                break
            else:
                barrier_corpus += ". "
        return barrier_corpus

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

        barrier_similarity_scores = self[barrier_id].sort_values(ascending=False)[
            :limit
        ]
        barrier_similarity_scores = barrier_similarity_scores[
            barrier_similarity_scores > threshold
        ]
        barrier_queryset = Barrier.objects.filter(
            id__in=barrier_similarity_scores.index
        )
        return barrier_queryset


class BarrierEmbeddingDict(UserDict):
    """Dictionary for storing and retrieving barrier embeddings.

    Uses torch.load/save for serialisation."""

    barrier_embeddings_dict_path = os.path.join(
        settings.ROOT_DIR, "barrier_embeddings_dict.pkl"
    )

    def __init__(self):
        """Initialise the dictionary either with the cached version, the version on disk, or create a new one."""
        if cached_barrier_embeddings_dict := cache.get(
            settings.BARRIER_EMBEDDINGS_DICT_CACHE_KEY
        ):
            super().__init__(cached_barrier_embeddings_dict)
        else:
            if os.path.isfile(self.barrier_embeddings_dict_path):
                with open(self.barrier_embeddings_dict_path, "rb") as f:
                    super().__init__(torch.load(f))
            else:
                # we need to create it
                super().__init__()  # creating empty dict
                # computing the embeddings for each barrier and saving to dictionary
                for barrier_object in Barrier.objects.exclude(draft=True):
                    self[
                        str(barrier_object.id)
                    ] = SimilarityScoreMatrix.compute_barrier_embedding(barrier_object)
                self.save_dict()  # saving to disk

    def __getitem__(self, key):
        """Get the barrier embedding for a barrier id.

        If the barrier ID is not in the dictionary, compute the embedding and save it to the dictionary."""
        try:
            return super().__getitem__(key)
        except KeyError:
            barrier_object = Barrier.objects.get(id=key)
            self[key] = SimilarityScoreMatrix.compute_barrier_embedding(barrier_object)
            self.save_dict()
            return super().__getitem__(key)

    def save_dict(self):
        """Save the barrier embeddings dictionary to disk and cache."""
        cache.set(
            settings.BARRIER_EMBEDDINGS_DICT_CACHE_KEY,
            self.data,
            timeout=None,
        )

        torch.save(self.data, self.barrier_embeddings_dict_path)
