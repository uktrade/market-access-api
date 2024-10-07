import os
import time

import requests
from django.core.management import BaseCommand
from api.related_barriers import client
from api.barriers.models import Barrier


class Command(BaseCommand):
    help = "Attach policy teams to barriers"

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=bool, help="Seed related barriers service")
        parser.add_argument("--test", type=bool, help="Seed related barriers service")

    def handle(self, *args, **options):
        seed = options["seed"]
        test = options["test"]

        if seed:
            print('Seeding related barriers service ...')
            start = time.time()
            client.seed()
            end = time.time()
            print(f'Seeded in {end - start}s')

        if test:
            qs = Barrier.objects.order_by("-created_on")

            for b in qs[10:43]:
                print(b.title)

            import csv

            entries = []
            cleaned_entries = []


            import spacy
            nlp = spacy.load("en_core_web_sm")

            with open('/usr/src/app/api/related_barriers/management/commands/data.csv') as csvfile:
                spamreader = csv.reader(csvfile, delimiter='#')
                for barrier, row in zip(qs[10:43], spamreader):
                    print(barrier.id, len(row))
                    raw_text = f"{row[0]} . {row[1]}"
                    entries.append(
                        {
                            "barrier_id": str(barrier.id),
                            "corpus": raw_text
                        }
                    )
                    cleaned_entries.append(
                        {
                            "barrier_id": str(barrier.id),
                            "corpus": " ".join([t.text for t in nlp(raw_text) if not t.is_stop])
                        }
                    )


            requests.post(
                f"{os.environ['RELATED_BARRIERS_BASE_URL']}/seed",
                json={
                    "data": entries
                },
            )
            res = requests.get(
                f"{os.environ['RELATED_BARRIERS_BASE_URL']}/cosine-similarity",
            )

            print(res.json())

            requests.post(
                f"{os.environ['RELATED_BARRIERS_BASE_URL']}/seed",
                json={
                    "data": cleaned_entries
                },
            )
            res2 = requests.get(
                f"{os.environ['RELATED_BARRIERS_BASE_URL']}/cosine-similarity",
            )

            print(res2.json())

            print(entries[0])
            print(cleaned_entries[0])
