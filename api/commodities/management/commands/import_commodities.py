import csv

from django.core.management import BaseCommand
from django.conf import settings

from api.commodities.models import Commodity


class Command(BaseCommand):
    help = "Import commodities"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="CSV file")
        parser.add_argument("--version-date", type=str, help="Version (ISO-8601 date)")

    def handle(self, *args, **options):
        self.import_commodities(options["file"], options["version-date"])
        self.add_parents(options["file"], options["version-date"])

    def import_commodities(self, csv_file, version):
        self.stdout.write("Importing commodities...")

        with open(csv_file, 'r' ) as file:
            reader = csv.DictReader(file)
            i = 0
            for line in reader:
                commodity = Commodity.objects.create(
                    version=version,
                    code=line["Commodity code"],
                    suffix=line["Suffix"],
                    level=line["HS Level"],
                    indent=line["Indent"],
                    description=line["Description"],
                    is_leaf=(line["Suffix"] == "80"),
                    sid=line["SID"],
                    parent_sid=line["Parent SID"] or None,
                )

                if i % 1000 == 0:
                    self.stdout.write(str(i))

                i += 1

    def add_parents(self, csv_file, version):
        self.stdout.write("Adding parents...")
        i = 0
        for commodity in Commodity.objects.filter(parent_sid__isnull=False, version=version):
            commodity.parent = Commodity.objects.get(sid=commodity.parent_sid, version=version)
            commodity.save()

            if i % 1000 == 0:
                self.stdout.write(str(i))

            i += 1
