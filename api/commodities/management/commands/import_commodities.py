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
        self.add_parents(options["version_date"])

    def import_commodities(self, csv_file, version):
        self.stdout.write("Importing commodities...")

        with open(csv_file, "r") as file:
            reader = csv.DictReader(file)
            i = 0
            for line in reader:
                if not line.get("commodity_code", None):
                    return
                commodity = Commodity.objects.create(
                    version=version,
                    code=self.clean_commodity_code(line["commodity_code"], version),
                    suffix=line["suffix"],
                    level=line["hs_level"],
                    indent=line["indent"],
                    description=line["description"],
                    is_leaf=line["suffix"] == "80",
                    sid=line.get("sid", None) or None,
                    parent_sid=line.get("parent_sid", None) or None,
                    parent_code=self.clean_commodity_code(
                        line["commodity_code"], version
                    )
                    or None,
                )

                if i % 1000 == 0:
                    self.stdout.write(str(i))

                i += 1

    def clean_commodity_code(self, commodity_code, version):
        if version == "2022":
            commodity_code = f"{commodity_code}00"
        if len(commodity_code) < 10:
            commodity_code = f"0{commodity_code}"
        return commodity_code

    def add_parents(self, version):
        self.stdout.write("Adding parents...")
        i = 0
        for commodity in Commodity.objects.filter(
            parent_code__isnull=False, version=version
        ):
            parent = Commodity.objects.filter(
                code=commodity.parent_code, version=version
            )
            if parent.exists():
                commodity.parent = parent.first()
                commodity.save()

            if i % 1000 == 0:
                self.stdout.write(str(i))

            i += 1
