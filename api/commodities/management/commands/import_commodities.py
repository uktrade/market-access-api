import csv

from django.core.management import BaseCommand

from api.commodities.models import Commodity


class Command(BaseCommand):
    help = "Import commodities"

    def add_arguments(self, parser):
        parser.add_argument("--file", type=str, help="CSV file")
        parser.add_argument("--version_date", type=str, help="Version (ISO-8601 date)")

    def handle(self, *args, **options):
        self.import_commodities(options["file"], options["version_date"])
        self.add_parents(options["file"], options["version_date"])

    def import_commodities(self, csv_file, version):
        self.stdout.write("Importing commodities...")

        with open(csv_file, "r") as file:
            reader = csv.DictReader(file)
            i = 0
            for line in reader:
                if "Number of rows" in line["id"]:
                    return
                commodity_code = line["commodity_code"]
                if len(commodity_code) < 10:
                    commodity_code = f"0{commodity_code}"
                commodity = Commodity.objects.create(
                    version=version,
                    code=commodity_code,
                    suffix=line["suffix"],
                    level=line["hs_level"],
                    indent=line["indent"],
                    description=line["description"],
                    is_leaf=(line["suffix"] == "80"),
                    sid=line["sid"],
                    parent_sid=line["parent_sid"] or None,
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
            try:
                commodity.parent = Commodity.objects.get(
                sid=commodity.parent_sid, version=version
            )
            except:
                commodity.parent = None
            commodity.save()

            if i % 1000 == 0:
                self.stdout.write(str(i))

            i += 1
