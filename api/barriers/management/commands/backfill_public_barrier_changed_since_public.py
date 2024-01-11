from django.core.management import BaseCommand

from api.barriers.models import Barrier, PublicBarrier


class Command(BaseCommand):
    help = "Backfill PublicBarrier changed_since_published field"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", type=bool, default=False, required=False)

    def handle(self, *args, **options):
        public_barriers = PublicBarrier.objects.filter(
            changed_since_public=False
        ).values_list("barrier__id", "last_published_on")

        dry_run = options["dry_run"]

        print(f"Public Barrier Count: {public_barriers.count()}")
        for barrier in public_barriers:
            print(barrier)
            if barrier[1] is not None:
                barrier_history = Barrier.history.filter(
                    id=barrier[0], history_date__lt=barrier[1]
                ).values_list("categories_cache", "title", "summary")
                print(
                    f"Public Barrier {barrier[0]} History Count: {barrier_history.count()}"
                )

                for i, historical_record in enumerate(barrier_history):
                    if i == len(barrier_history) - 1:
                        break

                    if any(
                        [
                            historical_record[0] == barrier_history[i + 1][0],
                            historical_record[1] == barrier_history[i + 1][1],
                            historical_record[2] == barrier_history[i + 1][2],
                        ]
                    ):
                        changed = True
                        break

                if changed:
                    print(f"Barrier {barrier[0]} changed")
                    if not dry_run:
                        PublicBarrier.objects.get(barrier=barrier[0]).update(
                            changed_since_public=True
                        )
