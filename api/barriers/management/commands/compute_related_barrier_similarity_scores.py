from django.core.management import BaseCommand

from api.barriers.related_barrier import SimilarityScoreMatrix


class Command(BaseCommand):
    help = "Compute and store all barrier similarity scores"

    def handle(self, *args, **options):
        SimilarityScoreMatrix.create_matrix()
