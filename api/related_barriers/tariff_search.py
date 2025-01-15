import logging

# import pandas as pd
import requests
import torch
from django.core.cache import cache
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class TariffSearchManager:
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    TARIFF_EMBEDDINGS_CACHE_KEY = "TARIFF_EMBEDDINGS_CACHE_KEY"
    COMMODITY_CACHE_KEY = "COMMODITY_CACHE_KEY"

    def get_commodities_list(self):
        # Get all sections
        sections_url = "https://www.trade-tariff.service.gov.uk/api/v2/sections"
        sections_response = requests.get(
            sections_url,
        )

        # Loop each section, use the ID to do the call to get to goods list for a section
        commodity_embed_list = []
        commodity_lookup_list = []
        for section in sections_response.json()["data"]:
            logger.critical(section["id"])

            goods_url = f"https://www.trade-tariff.service.gov.uk/api/v2/goods_nomenclatures/section/{section['id']}"

            goods_response = requests.get(
                goods_url,
            )

            # df = pd.DataFrame.from_dict(goods_response.json()["data"])
            # print(df)

            # goods_count = 0

            # For each commodity in the response, add the formatted description to the data list
            for commodity in goods_response.json()["data"]:
                # logger.critical("-")
                # logger.critical(commodity)
                # logger.critical("-")
                if commodity["attributes"]["formatted_description"] != "Other":
                    # Add item to both the lookup list and the list that will serve as the embedding
                    commodity_embed_list.append(
                        commodity["attributes"]["formatted_description"]
                    )
                    commodity_lookup_list.append(
                        {
                            "description": commodity["attributes"][
                                "formatted_description"
                            ],
                            "hs_code": commodity["attributes"][
                                "goods_nomenclature_item_id"
                            ],
                        }
                    )
                # goods_count = goods_count+1
                # if goods_count > 10:
                #    break
            # if goods_count > 10:
            #    break

        corpus_embeddings = self.embedder.encode(
            commodity_embed_list, convert_to_tensor=True
        )
        self.store_embeddings(corpus_embeddings)
        self.store_commodity_list(commodity_lookup_list)

    def store_embeddings(self, embeddings):
        logger.info("(Tariff Search): store_embeddings")
        cache.set(self.TARIFF_EMBEDDINGS_CACHE_KEY, embeddings, timeout=None)

    def get_embeddings(self):
        logger.info("(Tariff Search): get_embeddings")
        return cache.get(self.TARIFF_EMBEDDINGS_CACHE_KEY, [])

    def store_commodity_list(self, commodities):
        logger.info("(Tariff Search): store_commodity_list")
        cache.set(self.COMMODITY_CACHE_KEY, commodities, timeout=None)

    def get_commodity_list(self):
        logger.info("(Tariff Search): get_commodity_list")
        return cache.get(self.COMMODITY_CACHE_KEY, [])

    def flush(self):
        logger.info("(Tariff Search): flush cache")
        cache.delete(self.TARIFF_EMBEDDINGS_CACHE_KEY)
        cache.delete(self.COMMODITY_CACHE_KEY)

    def get_similarities(self, query):

        # Get the tensor value for the query passed to API
        query_embedding = self.embedder.encode(query, convert_to_tensor=True)

        # Get the stored commodity embeddings
        stored_embeddings = self.get_embeddings()

        # Get the similarity scores
        similarity_scores = self.embedder.similarity(
            query_embedding, stored_embeddings
        )[0]

        scores, indices = torch.topk(similarity_scores, k=20)

        # Get the lookup list holding the description and HS code of commodities.
        # list index matches the embedding list
        commodity_lookup_list = self.get_commodity_list()

        # Build a result list to pass back to frontend
        response_list = []
        for score, idx in zip(scores, indices):
            commodity = commodity_lookup_list[idx]
            response_list.append(
                {
                    "hs_code": commodity["hs_code"],
                    "description": commodity["description"],
                    "similarity": score,
                }
            )

        # Gives identical results
        # hits = SearchTest.semantic_search(query_embedding, stored_embeddings, top_k=20)
        # hits = hits[0]      #Get the hits for the first query
        # logger.critical("----------------")
        # for hit in hits:
        #    logger.critical(str(commodity_lookup_list[hit['corpus_id']]) + " " + str(hit['score']))
        # logger.critical("----------------")

        return response_list
