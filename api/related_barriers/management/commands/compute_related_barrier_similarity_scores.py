from django.core.management import BaseCommand

from api.related_barriers.service import SimilarityScoreMatrix


class Command(BaseCommand):
    help = "Compute and store all barrier similarity scores"

    def handle(self, *args, **options):
        SimilarityScoreMatrix.create_matrix()
