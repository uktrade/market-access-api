import os
from typing import List, Dict

import requests

from api.barriers.tasks import get_barriers_overseas_region
from api.metadata.utils import get_sector


def get_data() -> List[Dict]:
    from api.barriers.models import Barrier

    data_dictionary = []
    barriers = (
        Barrier.objects.prefetch_related("interactions_documents")
        .filter(archived=False)
        .exclude(draft=True)
    )
    for barrier in barriers:
        data_dictionary.append(
            {"id": str(barrier.id), "barrier_corpus": barrier_to_corpus(barrier)}
        )

    return data_dictionary


def barrier_to_corpus(barrier) -> str:
    companies_affected_list = ""
    if barrier.companies:
        companies_affected_list = ", ".join(
            [company["name"] for company in barrier.companies]
        )

    other_organisations_affected_list = ""
    if barrier.related_organisations:
        other_organisations_affected_list = ", ".join(
            [company["name"] for company in barrier.related_organisations]
        )

    notes_text_list = ", ".join(
        [note.text for note in barrier.interactions_documents.all()]
    )

    sectors_list = [
        get_sector(str(sector_id))["name"]
        for sector_id in barrier.sectors
        if get_sector(str(sector_id))
    ]
    sectors_list.append(get_sector(barrier.main_sector)["name"])
    sectors_text = ", ".join(sectors_list)

    overseas_region_text = get_barriers_overseas_region(
        barrier.country, barrier.trading_bloc
    )

    estimated_resolution_date_text = ""
    if barrier.estimated_resolution_date:
        date = barrier.estimated_resolution_date.strftime("%d-%m-%Y")
        estimated_resolution_date_text = f"Estimated to be resolved on {date}."

    return (
        f"{barrier.title}. {barrier.summary}. "
        f"{sectors_text} {barrier.country_name}. "
        f"{overseas_region_text}. {companies_affected_list} "
        f"{other_organisations_affected_list} {notes_text_list}. "
        f"{barrier.status_summary}. {estimated_resolution_date_text}. "
        f"{barrier.export_description}."
    )


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
    data = get_data()
    import spacy
    nlp = spacy.load("en_core_web_sm")



    print("Num barriers: ", len(data))
    print("Example barrier: ", data[0])
    lines = []
    for d in data:
        doc = nlp(d["barrier_corpus"])
        filtered_tokens = [token.text for token in doc if not token.is_stop]
        lines.append({"barrier_id": str(d["id"]), "corpus": " ".join(filtered_tokens)})

    print(lines[0])

    requests.post(
        f"{os.environ['RELATED_BARRIERS_BASE_URL']}/seed",
        json={
            "data": lines
        },
    )


def get_related_barriers(pk, title, summary):
    res = requests.post(
        f"{os.environ['RELATED_BARRIERS_BASE_URL']}/related-barriers",
        json={"barrier_id": f"{pk}", "corpus": f"{title}. {summary}"},
    )
    return res.json()["results"]
