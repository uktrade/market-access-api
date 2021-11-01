import csv

from django.core.management import BaseCommand

from api.commodities.models import Commodity


class Command(BaseCommand):
    help = "Import commodities"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="CSV file")
        parser.add_argument("--version-date", type=str, help="Version (ISO-8601 date)")

    def handle(self, *args, **options):
        self.import_commodities(options["file"], options["version_date"])
        self.add_parents(options["file"], options["version_date"])

    def import_commodities(self, csv_file, version):
        self.stdout.write("Importing commodities...")

        with open(csv_file, "r") as file:
            reader = csv.DictReader(file)
            i = 0
            for line in reader:
                padded_code = line["Commodity code"].ljust(10, "0")
                if Commodity.objects.filter(code=padded_code).count() == 0:
                    # only create new commodity if it does not already exist
                    commodity = Commodity.objects.create(
                        version=version,
                        code=line["Commodity code"].ljust(10, "0"),
                        suffix=line["Suffix"],
                        level=line["HS Level"],
                        indent=line["Indent"],
                        description=line["Description"],
                        is_leaf=(line["Suffix"] == "80"),
                        sid=line["SID"],
                        parent_sid=line["Parent SID"] or None,
                        classification=line.get("Classification", "H5"),
                    )

                if i % 1000 == 0:
                    self.stdout.write(str(i))

                i += 1

    def add_parents(self, csv_file, version):
        self.stdout.write("Adding parents...")
        i = 0
        for commodity in Commodity.objects.filter(
            parent_sid__isnull=False, version=version
        ):
            commodity.parent = Commodity.objects.get(
                sid=commodity.parent_sid, version=version
            )
            commodity.save()

            if i % 1000 == 0:
                self.stdout.write(str(i))

            i += 1
