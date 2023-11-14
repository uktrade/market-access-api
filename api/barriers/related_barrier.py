import re
import typing

import numpy as np
from sentence_transformers import SentenceTransformer, util

# Precompiled patterns
NON_WORD_PATTERN = re.compile(r"\W")  # Matches any non-word character
SINGLE_CHAR_PATTERN = re.compile(r"\s+[a-z]\s+")  # Matches all single characters

SIMILARITY_THRESHOLD = 0.4

# https://www.sbert.net/docs/pretrained_models.html
# Load the sentence transformer model
# albert-small-v2 # 43 MB size
# smaller model
transformer_model = SentenceTransformer("paraphrase-MiniLM-L3-v2")


class QuerySet(typing.Protocol):
    def values(self):
        ...


class ValuesQuerySet(typing.Protocol):
    def last(self):
        ...


class DataFrame(typing.Protocol):
    def __init__(self, *args, **kwargs):
        ...

    def from_records(self, *args, **kwargs):
        ...


def preprocess_text(text: str) -> str:
    """
    function to preprocess text before it is saved to the database
    """
    text = str(text).lower()
    # remove all non-word characters & all single characters
    text = NON_WORD_PATTERN.sub(" ", SINGLE_CHAR_PATTERN.sub(" ", text))
    return text


def query_set_to_pandas_df(queryset: QuerySet) -> DataFrame:
    """
    function to convert a django query set to a pandas dataframe
    """
    import pandas as pd

    return pd.DataFrame.from_records(queryset.values())


def __get_similar_barriers(
    title_row: DataFrame, barrier_id: str, df: DataFrame, n: int
) -> DataFrame:
    """
    function to get similar barriers based on cosine similarity
    """

    # Obtain embeddings for each processed_text
    df["embeddings"] = df["processed_text"].apply(lambda x: transformer_model.encode(x))

    # Create a matrix of the embeddings
    embeddings_matrix = np.vstack(df["embeddings"].to_numpy())

    # Obtain embeddings for title
    title_embeddings = transformer_model.encode(title_row["processed_text"].values[0])

    # Calculate cosine similarity between title and all other processed_text
    cosine_scores = util.cos_sim(title_embeddings, embeddings_matrix)[0]

    # Add cosine scores to dataframe
    df["similarity"] = cosine_scores

    # Sort dataframe by cosine scores
    df = df[df["similarity"] > SIMILARITY_THRESHOLD].sort_values(
        by=["similarity"], ascending=False
    )

    df = df[df["id"] != barrier_id]

    return df.head(n)


def get_similar_barriers(
    values_query_set: ValuesQuerySet, barrier_id: str, n: int
) -> DataFrame:

    df = query_set_to_pandas_df(values_query_set)

    df["processed_text"] = df["summary"].apply(lambda x: preprocess_text(x))

    # Check if title exists in data
    title_row = df[df["id"] == barrier_id].copy()

    if title_row.empty:
        raise ValueError("Barrier ID not found in data")

    df = __get_similar_barriers(title_row, barrier_id, df, n)

    return df
