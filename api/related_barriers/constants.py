from collections import namedtuple

SIMILARITY_THRESHOLD: float = 0.19
SIMILAR_BARRIERS_LIMIT: int = 5

"""
BarrierEntry is the data type used by the RelatedBarrierManager
"""
BarrierEntry = namedtuple("BarrierEntry", "id barrier_corpus")
