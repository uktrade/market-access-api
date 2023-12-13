import json
import pickle

import pandas as pd
from django.core.management import BaseCommand
from sentence_transformers import util

from api.barriers.related_barrier import (
    get_annotated_barrier_queryset,
    transformer_model,
)


class Command(BaseCommand):
    help = "Compute and store all barrier similarity scores"

    def handle(self, *args, **options):
        barriers = get_annotated_barrier_queryset()
        barrier_embeddings_df = pd.DataFrame.from_records(
            barriers.values("id", "barrier_corpus")
        )
        barrier_embeddings_df["embeddings"] = barrier_embeddings_df[
            "barrier_corpus"
        ].apply(lambda x: transformer_model.encode(x, convert_to_tensor=True))
        barrier_embeddings_dict = barrier_embeddings_df.set_index("id").T.to_dict()
        with open("barrier_embeddings_dict.json", "w") as f:
            json.dump(barrier_embeddings_dict, f)

        # creating the similarity scores dataframe matrix
        barrier_ids = barrier_embeddings_df["id"].to_list()
        similarity_scores_df = pd.DataFrame(index=barrier_ids, columns=barrier_ids)

        for index, row in barrier_embeddings_df.iterrows():
            current_barrier_id = row["id"]
            current_barrier_embeddings = row["embeddings"]

            similarity_scores_matrix_row = similarity_scores_df.loc[current_barrier_id]
            for index, relevant_barrier_similarity_score in enumerate(
                similarity_scores_matrix_row
            ):
                # looping over every barrier again except for this one
                relevant_barrier_id = barrier_ids[index]
                similarity_score = util.cos_sim(
                    current_barrier_embeddings,
                    barrier_embeddings_df[
                        barrier_embeddings_df["id"] == relevant_barrier_id
                    ]["embeddings"][index],
                )
                similarity_scores_df[current_barrier_id][index] = similarity_score
                print(similarity_score)

        print("All barrier similarity scores computed, saving to pickle")
        similarity_scores_df.to_pickle("barrier_similarity_scores_df.pkl")
