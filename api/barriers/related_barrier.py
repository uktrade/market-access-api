import numpy as np
import pandas as pd
from django.db.models import QuerySet
from sentence_transformers import SentenceTransformer, util

SIMILARITY_THRESHOLD = 0.19

# https://www.sbert.net/docs/pretrained_models.html
# Load the sentence transformer model
# albert-small-v2 # 43 MB size
# smaller model
transformer_model = SentenceTransformer("paraphrase-MiniLM-L3-v2")


def query_set_to_pandas_df(queryset: QuerySet) -> pd.DataFrame:
    """
    function to convert a django query set to a pandas dataframe
    """

    return pd.DataFrame.from_records(queryset.values())


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
    df = query_set_to_pandas_df(values_query_set)

    # Getting the barrier row from the dataframe
    barrier_row = df[df["id"] == barrier_id].copy()

    # Check if title exists
    if barrier_row.empty:
        raise ValueError("Barrier ID not found in data")

    df = __get_similar_barriers(barrier_row, barrier_id, df, limit)

    return df
