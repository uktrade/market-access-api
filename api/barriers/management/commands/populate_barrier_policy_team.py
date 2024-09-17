import csv
from collections import defaultdict

from django.core.management import BaseCommand

from api.barriers.models import Barrier


class Command(BaseCommand):
    help = "Attach policy teams to barriers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--filepath", type=str, help="Path to barrier policy csv file."
        )
        parser.add_argument(
            "--dryrun", type=bool, help="Run without persisting results"
        )

    def handle(self, *args, **options):
        filepath = options["filepath"]
        dryrun = options["dryrun"]
        with open(filepath) as csvfile:
            reader = csv.reader(csvfile)
            objects = []

            for row in reader:
                objects.append((row[0], row[1]))

            barrier_codes = [o[0] for o in objects]
            barrier_code_to_id = {
                b["code"]: str(b["id"])
                for b in Barrier.objects.filter(code__in=barrier_codes).values(
                    "id", "code"
                )
            }
            barrier_policy_teams = [(barrier_code_to_id[o[0]], o[1]) for o in objects]

            barrier_to_policy_team = defaultdict(list)
            for barrier_code, policy_team_id in barrier_policy_teams:
                if policy_team_id not in barrier_to_policy_team[barrier_code]:
                    barrier_to_policy_team[barrier_code].append(int(policy_team_id))
                else:
                    print("Duplicate entry: ", (barrier_code, policy_team_id))

            for barrier_id, policy_team_ids in barrier_to_policy_team.items():
                barrier = Barrier.objects.get(id=barrier_id)
                if dryrun:
                    print(f"{barrier_id}: {policy_team_ids}")
                else:
                    for pid in policy_team_ids:
                        barrier.policy_teams.add(pid)
