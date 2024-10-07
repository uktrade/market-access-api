import os
import requests


def seed_data():
    from django.db.models import CharField
    from django.db.models import Value as V
    from django.db.models.functions import Concat
    from api.barriers.models import Barrier

    return (
        Barrier.objects.filter(archived=False)
        .exclude(draft=True)
        .annotate(
            barrier_corpus=Concat("title", V(". "), "summary", output_field=CharField())
        )
        .values("id", "barrier_corpus")
    )


def seed():
    data = seed_data()

    requests.post(
        f"{os.environ['RELATED_BARRIERS_BASE_URL']}/seed",
        json={
            "data": [
                {"barrier_id": str(d["id"]), "corpus": d["barrier_corpus"]}
                for d in data
            ]
        },
    )


def get_related_barriers(pk, title, summary):
    res = requests.post(
        f"{os.environ['RELATED_BARRIERS_BASE_URL']}/related-barriers",
        json={"barrier_id": f"{pk}", "corpus": f"{title}. {summary}"},
    )
    results = res.json()["results"]
    return [b["barrier_id"] for b in results]
