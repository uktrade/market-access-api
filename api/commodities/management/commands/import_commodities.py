import csv

from django.core.management import BaseCommand
from django.conf import settings

from api.commodities.models import Commodity


class Command(BaseCommand):
    help = "Import commodities"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str, help="CSV file")

    def handle(self, *args, **options):
        self.import_commodities(options["file"])
        self.add_parents(options["file"])

    def import_commodities(self, csv_file):
        self.stdout.write("Importing commodities...")

        with open(csv_file, 'r' ) as file:
            reader = csv.DictReader(file)
            i = 0
            for line in reader:
                commodity = Commodity.objects.create(
                    code=line["Commodity code"],
                    suffix=line["Suffix"],
                    level=line["HS Level"],
                    indent=line["Indent"],
                    description=line["Description"],
                )

                if i % 500 == 0:
                    self.stdout.write(str(i))

                i += 1

    def add_parents(self, csv_file):
        self.stdout.write("Adding parents...")

        with open(csv_file, 'r' ) as file:
            reader = csv.DictReader(file)
            i = 0
            for line in reader:
                commodity = Commodity.objects.get(code=line["Commodity code"])
                parent_code = line["Parent code"]

                if parent_code:
                    try:
                        commodity.parent = Commodity.objects.get(code=parent_code)
                        commodity.save()
                    except Commodity.DoesNotExist:
                        self.stdout.write("Unable to find parent for: ", line["Commodity code"])

                if i % 500 == 0:
                    self.stdout.write(str(i))

                i += 1
