from django.core.management import BaseCommand
from api.barriers.models import Barrier
from api.barriers.tasks import get_barriers_overseas_region
from api.interactions.models import Interaction
from api.metadata.utils import get_sector
from api.related_barriers.views import related_barriers, related_barriers_search

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):

    # ./manage.py run_search_related_test --searchterm 'Company called BARCLAYS PLC is affected by this barrier'

    help = "Test the related barriers engine with a search term"

    def add_arguments(self, parser):
        parser.add_argument("--searchterm", type=str, help="Search term to use")

    def handle(self, *args, **options):
        logger.critical("+++++++++")
        logger.critical("Start Test")
        logger.critical(options["searchterm"])
        logger.critical("+++++++++")

        logger.critical("SCORES -----")
        response_data = related_barriers_search("request_dummy",options["searchterm"],log_score=True)
        logger.critical("------------")

        for bar_id in response_data:#[-6:]:
            if bar_id != "search_term":
                logger.critical("-")
                barrier_detail = Barrier.objects.get(pk=bar_id)
                logger.critical("ID = " + str(bar_id))
                logger.critical("TITLE = "+ str(barrier_detail.title))
                logger.critical("SUMMARY = "+ str(barrier_detail.summary))
                sectors_list = [get_sector(sector)["name"] for sector in barrier_detail.sectors]
                logger.critical("SECTORS = "+ str(get_sector(barrier_detail.main_sector)["name"]) + " " + str(sectors_list))
                logger.critical("COUNTRY = "+ str(get_barriers_overseas_region(barrier_detail.country, barrier_detail.trading_bloc)))
                logger.critical("COMPANIES = "+ str(barrier_detail.companies))
                logger.critical("OTHER COMPANIES = "+ str(barrier_detail.related_organisations))
                logger.critical("STATUS SUMMARY = "+ str(barrier_detail.status_summary))
                logger.critical("EST. RESOLUTION DATE = "+ str(barrier_detail.estimated_resolution_date))
                logger.critical("EXPORT DESC. = "+ str(barrier_detail.export_description))
                notes_list = [note.text for note in barrier_detail.interactions_documents.all()]
                logger.critical("NOTES = "+ str(notes_list))
                logger.critical("-")

        logger.critical("+++++++++")
        logger.critical("End Test")
        logger.critical("+++++++++")
