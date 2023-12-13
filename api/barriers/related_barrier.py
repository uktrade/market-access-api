import os

import numpy as np
import pandas as pd
from django.conf import settings
from django.db.models import CharField, QuerySet
from django.db.models import Value as V
from django.db.models.functions import Concat
from sentence_transformers import SentenceTransformer, util

from api.barriers.models import Barrier

SIMILARITY_THRESHOLD = 0.19

# https://www.sbert.net/docs/pretrained_models.html
# Load the sentence transformer model
# albert-small-v2 # 43 MB size
# smaller model
transformer_model = SentenceTransformer("paraphrase-MiniLM-L3-v2")

RELEVANT_BARRIER_FIELDS = [
    "title",
    "summary",
]


def __get_similar_barriers(
    barrier_row: pd.DataFrame, barrier_id: str, df: pd.DataFrame, limit: int
) -> pd.DataFrame:
    """
    function to get similar barriers based on cosine similarity
    """

    # Obtain embeddings for each processed_text
    df["embeddings"] = df["barrier_corpus"].apply(
        lambda x: transformer_model.encode(x, convert_to_tensor=True)
    )

    # Create a matrix of the embeddings
    embeddings_matrix = np.vstack(df["embeddings"].to_numpy())

    # Obtain embeddings for title
    barrier_embeddings = transformer_model.encode(
        barrier_row["barrier_corpus"].values[0]
    )

    # Calculate cosine similarity between title and all other processed_text
    cosine_scores = util.cos_sim(barrier_embeddings, embeddings_matrix)[0]

    # Add cosine scores to dataframe
    df["similarity"] = cosine_scores

    # Sort dataframe by cosine scores
    df = df[df["similarity"] > SIMILARITY_THRESHOLD].sort_values(
        by=["similarity"], ascending=False
    )

    # removing the barrier itself from the dataframe
    df = df[df["id"] != barrier_id]

    # trimming the dataframe according to the defined limit
    return df.head(limit)


def get_similar_barriers(
    values_query_set: QuerySet, barrier_id: str, limit: int
) -> pd.DataFrame:
    df = pd.DataFrame.from_records(values_query_set.values())

    # Getting the barrier row from the dataframe
    barrier_row = df[df["id"] == barrier_id].copy()

    # Check if title exists
    if barrier_row.empty:
        raise ValueError("Barrier ID not found in data")

    df = __get_similar_barriers(barrier_row, barrier_id, df, limit)

    return df


def get_annotated_barrier_queryset():
    annotation_args = []
    for index, field in enumerate(RELEVANT_BARRIER_FIELDS):
        annotation_args.append(field)
        if index == len(RELEVANT_BARRIER_FIELDS) - 1:
            break
        else:
            annotation_args.append(V(". "))
    return Barrier.objects.exclude(draft=True).annotate(
        barrier_corpus=Concat(*annotation_args, output_field=CharField())
    )


def update_similarity_score_matrix(
    barrier_object, similarity_scores_df=None, barrier_embeddings_df=None
):
    if not similarity_scores_df:
        similarity_scores_df = pd.read_pickle(
            os.path.join(settings.ROOT_DIR, "barrier_similarity_scores_df.pkl")
        )

    if not barrier_embeddings_df:
        barrier_embeddings_df = pd.read_pickle(
            os.path.join(settings.ROOT_DIR, "barrier_embeddings_df.pkl")
        )

    barrier_corpus = ""
    for index, field in enumerate(RELEVANT_BARRIER_FIELDS):
        barrier_corpus += getattr(barrier_object, field)
        if index == len(RELEVANT_BARRIER_FIELDS) - 1:
            break
        else:
            barrier_corpus += ". "

    barrier_embedding = transformer_model.encode(barrier_corpus, convert_to_tensor=True)

    if barrier_object.id not in similarity_scores_df.columns:
        # this is a new barrier, so we need to add a new column to the similarity scores dataframe
        similarity_scores_df[barrier_object.id] = np.nan

    if not barrier_embeddings_df.loc(barrier_embeddings_df["id"] == barrier_object.id):
        # this is a new barrier, so we need to add a new row to the barrier embeddings dataframe
        barrier_embeddings_df = barrier_embeddings_df.append(
            {
                "id": barrier_object.id,
                "barrier_corpus": barrier_corpus,
                "embeddings": barrier_embedding,
            },
            ignore_index=True,
        )

    for index, barrier in barrier_embeddings_df.iterrows():
        embedding = barrier["embeddings"]
        similarity_score = util.cos_sim(barrier_embedding, embedding)
        similarity_scores_df[barrier_object.id][index] = similarity_score

    similarity_scores_df.to_pickle("barrier_similarity_scores_df.pkl")
    barrier_embeddings_df.to_pickle("barrier_embeddings_df.pkl")


class SimilarityScoreMatrix(pd.DataFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.similarity_scores_df = pd.read_pickle(
            os.path.join(settings.ROOT_DIR, "barrier_similarity_scores_df.pkl")
        )
        self.barrier_embeddings = pd.read_pickle(
            os.path.join(settings.ROOT_DIR, "barrier_embeddings.pkl")
        )

    def get_similar_barriers(self, barrier_id: str, limit: int) -> pd.DataFrame:
        barrier_row = self.loc[barrier_id]
        df = self[self[barrier_id] > SIMILARITY_THRESHOLD].sort_values(
            by=[barrier_id], ascending=False
        )

        # removing the barrier itself from the dataframe
        df = df[df["id"] != barrier_id]

        # trimming the dataframe according to the defined limit
        return df.head(limit)
