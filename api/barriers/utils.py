import re
import datetime
import numpy as np
from random import randrange

from django.conf import settings

from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords

from sentence_transformers import SentenceTransformer, util

CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Precompiled patterns
NON_WORD_PATTERN = re.compile(r"\W")  # Matches any non-word character
SINGLE_CHAR_PATTERN = re.compile(r"\s+[a-z]\s+")  # Matches all single characters


# https://www.sbert.net/docs/pretrained_models.html
# Load the sentence transformer model
# albert-small-v2 # 43 MB size
# smaller model
transformer_model = SentenceTransformer("albert-small-v2")

ENGLISH_STOP_WORDS = set(stopwords.words("english"))


def random_barrier_reference() -> str:

    """
    function to produce a random reference number for barriers
    format: B-YY-XXXX
    where YY is year and Xs are random alpha-numerics
    """
    dd = datetime.datetime.now()
    ref_code = f"B-{str(dd.year)[-2:]}-"
    for i in range(settings.REF_CODE_LENGTH):
        ref_code += CHARSET[randrange(0, len(CHARSET))]
    return ref_code


def preprocess_text(text: str) -> str:
    """
    function to preprocess text before it is saved to the database
    """
    text = str(text).lower()
    # remove all non-word characters & all single characters
    text = NON_WORD_PATTERN.sub(" ", SINGLE_CHAR_PATTERN.sub(" ", text))

    # Tokenization
    tokens = word_tokenize(text)

    # Stemming
    stemmer = PorterStemmer()
    stemmed_tokens = {
        stemmer.stem(word) for word in tokens if word not in ENGLISH_STOP_WORDS
    }

    return " ".join(stemmed_tokens)


def query_set_to_pandas_df(queryset: "Queryset") -> "pd.DataFrame":
    """
    function to convert a django query set to a pandas dataframe
    """
    import pandas as pd

    return pd.DataFrame.from_records(queryset.values())


def get_similar_barriers(
    title_row: "pd.DataFrame", barrier_id: str, df: "pd.DataFrame", n: int
) -> "pd.DataFrame":
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
    df["cosine_scores"] = cosine_scores

    # Sort dataframe by cosine scores
    df = df.sort_values(by=["cosine_scores"], ascending=False)

    df = df[df["id"] != barrier_id]

    return df.head(n)
