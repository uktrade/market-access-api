import logging
import random
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from faker import Faker

from api.assessment.models import (
    EconomicAssessment,
    EconomicImpactAssessment,
    ResolvabilityAssessment,
    StrategicAssessment,
)
from api.barriers.models import (
    Barrier,
    BarrierNextStepItem,
    BarrierProgressUpdate,
    BarrierTopPrioritySummary,
    ProgrammeFundProgressUpdate,
    PublicBarrier,
)
from api.collaboration.models import TeamMember
from api.history.items.action_plans import AuthUser
from api.history.models import CachedHistoryItem
from api.interactions.models import Interaction, Mention, PublicBarrierNote
from api.metadata.models import BarrierTag, Category, Organisation
from api.metadata.utils import get_countries, get_sectors
from api.wto.models import WTOCommittee, WTOProfile

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Anonymise sensitive data on barriers in the DB created before given date"

    # Call this command with:
    # ./manage.py data_anonymise --barrier_cutoff_date dd-mm-yy
    # ./manage.py data_anonymise --barrier_id <UUID>
    # from shell.

    # Command uses Faker to create junk data which then replaces data which
    # may contain sensitive information. Faker has different "providers" to generate
    # different types of data.
    # https://faker.readthedocs.io/en/master/providers/baseprovider.html

    # ./manage.py data_anonymise --barrier_cutoff_date 01-01-23
    # ./manage.py data_anonymise --barrier_id e30d8422-d402-4436-a0bc-26eeba1cb52d

    def add_arguments(self, parser):
        parser.add_argument(
            "--barrier_cutoff_date",
            type=str,
            help="Date before which barriers will be anonymised. Format dd-mm-yy.",
        )

        parser.add_argument(
            "--barrier_id",
            type=str,
            help="Specify a single barrier for anonymisation",
        )

    def _get_dummy_user(self):
        # Development environments can use placeholder IDs that exist on those DBs
        # local will need to source a random user from the local DB

        if settings.DJANGO_ENV == "local":
            AuthUser = get_user_model()
            user_list = AuthUser.objects.all()
            random_pick = random.choice(user_list)
            return random_pick.id
        else:
            DUMMY_USER_PROFILES = [
                "3903",
                "3916",
                "3871",
                "3911",
            ]
            return random.choice(DUMMY_USER_PROFILES)

    def _anonymise_text_fields(self, barriers):  # noqa
        """
        Function to create junk strings and replace text fields with
        this randomised data.
        Fields that will be anonymised (if they have existing value):
            - title
            - summary
            - status_summary
            - archived_explanation
            - priority_summary
            - next_steps_summary
            - archived_reason
            - unarchived_reason
            - public_eligibility_summary
            - economic_assessment_eligibility_summary
            - commercial_value_explanation
            - top_priority_rejection_summary
            - estimated_resolution_date_change_reason
            - export_description
        """
        for barrier in barriers:

            # Change fields that are required to be on a barrier
            barrier.title = (
                Faker().word()
                + " "
                + Faker().word()
                + " blocked in "
                + str(barrier.location)
            )
            barrier.summary = Faker().paragraph(nb_sentences=3)

            # Change fields which may or may not be populated on the barrier
            if barrier.status_summary:
                barrier.status_summary = Faker().paragraph(nb_sentences=3)
            if barrier.archived_explanation:
                barrier.archived_explanation = Faker().paragraph(nb_sentences=2)
            if barrier.priority_summary:
                barrier.priority_summary = Faker().paragraph(nb_sentences=2)
            if barrier.next_steps_summary:
                barrier.next_steps_summary = Faker().paragraph(nb_sentences=2)
            if barrier.archived_reason:
                barrier.archived_reason = Faker().paragraph(nb_sentences=2)
            if barrier.unarchived_reason:
                barrier.unarchived_reason = Faker().paragraph(nb_sentences=2)
            if barrier.public_eligibility_summary:
                barrier.public_eligibility_summary = Faker().paragraph(nb_sentences=2)
            if barrier.economic_assessment_eligibility_summary:
                barrier.economic_assessment_eligibility_summary = Faker().paragraph(
                    nb_sentences=2
                )
            if barrier.commercial_value_explanation:
                barrier.commercial_value_explanation = Faker().paragraph(nb_sentences=2)
            if barrier.top_priority_rejection_summary:
                barrier.top_priority_rejection_summary = Faker().paragraph(
                    nb_sentences=2
                )
            if barrier.estimated_resolution_date_change_reason:
                barrier.estimated_resolution_date_change_reason = Faker().paragraph(
                    nb_sentences=2
                )
            if barrier.export_description:
                barrier.export_description = Faker().paragraph(nb_sentences=2)

            barrier.save()

    def _anonymise_complex_barrier_fields(self, barriers):  # noqa
        """
        Function to take fields more complex than a text field and either
        scramble or anonymise their contents.
        Fields that will be anonymised (if they have existing value):
            - companies
            - related_organisations
            - commercial_value
            - sectors
            - main_sector
            - categories
            - organisations
            - tags
        """
        for barrier in barriers:

            company_suffixes = [" CO.", " PLC.", " LTD.", " INC."]
            if barrier.companies:
                for company in barrier.companies:
                    company["name"] = (
                        Faker().word()
                        + " "
                        + Faker().word()
                        + random.choice(company_suffixes)
                    )
            if barrier.related_organisations:
                for organisation in barrier.related_organisations:
                    organisation["name"] = (
                        Faker().word()
                        + " "
                        + Faker().word()
                        + random.choice(company_suffixes)
                    )

            if barrier.commercial_value:
                barrier.commercial_value = random.randint(10000, 10000000000)

            if barrier.sectors:
                sectors_list = get_sectors()
                number_of_sectors = len(barrier.sectors)
                new_sectors_list = []
                i = 0
                while i < number_of_sectors:
                    random_pick = random.choice(sectors_list)
                    new_sectors_list.append(random_pick["id"])
                    i = i + 1
                barrier.sectors = new_sectors_list

            if barrier.main_sector:
                sectors_list = get_sectors()
                random_pick = random.choice(sectors_list)
                main_sector_updated = False
                while main_sector_updated is not True:
                    # Cannot have a main_sector that is in the other sectors list
                    if random_pick["id"] not in new_sectors_list:
                        barrier.main_sector = random_pick["id"]
                        main_sector_updated = True
                    else:
                        random_pick = random.choice(sectors_list)

            if barrier.categories:
                categories_list = Category.objects.all()
                number_of_categories = barrier.categories.count()
                barrier.categories.clear()
                i = 0
                while i < number_of_categories:
                    random_pick = random.choice(categories_list)
                    barrier.categories.add(random_pick)
                    i = i + 1

            if barrier.organisations:
                organisations_list = Organisation.objects.all()
                number_of_organisations = barrier.organisations.count()
                barrier.organisations.clear()
                i = 0
                while i < number_of_organisations:
                    random_pick = random.choice(organisations_list)
                    barrier.organisations.add(random_pick)
                    i = i + 1

            if barrier.tags:
                tags_list = BarrierTag.objects.all()
                number_of_tags = barrier.tags.count()
                barrier.tags.clear()
                i = 0
                while i < number_of_tags:
                    random_pick = random.choice(tags_list)
                    barrier.tags.add(random_pick)
                    i = i + 1

            barrier.save()

    def _scramble_date_fields(self, barriers):
        """
        Function to get date fields and add or subtract days to mask
        actual dates.
        """

    def _anonymise_users_data(self, barriers):
        """
        Function to replace real staff with dummy users.
        We can replace with our own accounts as we know they will be in
        all environments and are not involved in creating barrier data.
        Fields that need anonymising:
            - created_by_id
            - modified_by_id
            - archived_by_id
            - unarchived_by_id
            - proposed_estimated_resolution_date_user_id
        Also need to update the team members associated with the barrier,
        where we can use dummy profile IDs to replace the real users.
        """

        for barrier in barriers:

            # Change fields which indicate which users have amended
            # details on the barrier
            barrier.created_by_id = self._get_dummy_user()
            if barrier.modified_by_id:
                barrier.modified_by_id = self._get_dummy_user()
            if barrier.archived_by_id:
                barrier.archived_by_id = self._get_dummy_user()
            if barrier.unarchived_by_id:
                barrier.unarchived_by_id = self._get_dummy_user()
            if barrier.proposed_estimated_resolution_date_user_id:
                barrier.proposed_estimated_resolution_date_user_id = (
                    self._get_dummy_user()
                )

            barrier.save()

            # Change users who are listed as having a stake or
            # influence on the barrier in question.
            barrier_team_list = barrier.barrier_team.all()
            for team_member in barrier_team_list:
                new_member_id = self._get_dummy_user()
                TeamMember.objects.filter(id=team_member.id).update(user=new_member_id)

    def _clear_barrier_report_session_data(self, barriers):
        """
        Function to clear any data stored in the new_report_session_data
        field which could hold sensitive data which has not yet
        been committed to a completed barrier.
        """
        for barrier in barriers:
            barrier.new_report_session_data = ""
            barrier.save()

    def _clear_barrier_notes(self, barriers):
        """
        Function to clear any notes attached to the barrier
        """
        for barrier in barriers:
            barrier_notes = Interaction.objects.filter(barrier=barrier.pk)

            for note in barrier_notes:
                note.text = Faker().paragraph(nb_sentences=4)
                note_user = AuthUser.objects.get(id=self._get_dummy_user())
                note.created_by = note_user
                note.modified_by = note_user
                note.save()

                # Documents attached to notes could have personal identifiers in the filepath.
                for document in note.documents.all():
                    #
                    #
                    #
                    #
                    #
                    # NEED TO TEST THIS ON UAT/DEV
                    # Upload file on specific barrier, do it on note and WTO page.
                    # Run script on this one specific barrier.
                    # Check filenames are different.
                    #
                    #
                    #
                    #
                    #
                    document.path = Faker().word() + "/" + Faker().word() + ".pdf"
                    document.save()

            # Mentions attcheched to the barrier also need clearing
            barrier_mentions = Mention.objects.filter(id=barrier.pk)
            for mention in barrier_mentions:
                mention.email_used = "fake_email@fake_provider.com"
                mention.recipient = self._get_dummy_user()
                mention.text = Faker().paragraph(nb_sentences=1)
                mention.save()

    def _anonymise_public_data(self, barriers):
        """
        Function to replace public fields with anonymous data
        Fields that need anonymising:
            - _title
            - internal_title_at_update
            - _summary
            - internal_summary_at_update
        """
        for barrier in barriers:
            # Get the public barrier
            public_barrier = PublicBarrier.objects.get(barrier=barrier.id)

            # Change the details
            if public_barrier:
                if public_barrier._title:
                    public_barrier._title = (
                        Faker().word()
                        + " "
                        + Faker().word()
                        + " blocked in "
                        + str(barrier.location)
                    )
                if public_barrier.internal_title_at_update:
                    public_barrier.internal_title_at_update = (
                        Faker().word()
                        + " "
                        + Faker().word()
                        + " blocked in "
                        + str(barrier.location)
                    )
                if public_barrier._summary:
                    public_barrier._summary = Faker().paragraph(nb_sentences=4)
                if public_barrier.internal_summary_at_update:
                    public_barrier.internal_summary_at_update = Faker().paragraph(
                        nb_sentences=4
                    )

                # Save the public barrier
                public_barrier.save()

                # Find all the public barrier notes and clear the text therein
                public_barrier_notes = PublicBarrierNote.objects.filter(
                    public_barrier=public_barrier.id
                )
                for public_note in public_barrier_notes:
                    public_note.text = Faker().paragraph(nb_sentences=4)
                    public_note.save()

    def _anonymise_progress_updates(self, barriers):
        """
        Function to randomise the content of progress updates
        Fields that need anonymising:
            - update (BarrierProgressUpdate)
            - next_steps (BarrierProgressUpdate)
            - milestones_and_deliverables (ProgrammeFundProgressUpdate)
            - expenditure (ProgrammeFundProgressUpdate)
        """
        for barrier in barriers:
            top_100_progress_updates = BarrierProgressUpdate.objects.filter(
                barrier=barrier.id
            )
            for update in top_100_progress_updates:
                update.update = Faker().paragraph(nb_sentences=4)
                update.next_steps = Faker().paragraph(nb_sentences=4)
                update.save()

            programme_fund_progress_updates = (
                ProgrammeFundProgressUpdate.objects.filter(barrier=barrier.id)
            )
            for update in programme_fund_progress_updates:
                update.milestones_and_deliverables = Faker().paragraph(nb_sentences=4)
                update.expenditure = Faker().paragraph(nb_sentences=4)
                update.save()

    def _anonymise_next_step_items(self, barriers):
        """
        Function to randomise the content of next step items
        Fields that need anonymising:
            - next_step_owner
            - next_step_item
        """
        for barrier in barriers:
            next_step_items = BarrierNextStepItem.objects.filter(barrier=barrier.id)
            for next_step_item in next_step_items:
                next_step_item.next_step_owner = Faker().word() + " " + Faker().word()
                next_step_item.next_step_item = Faker().paragraph(nb_sentences=4)
                next_step_item.save()

    def _anonymise_top_priority_data(self, barriers):
        """
        Function to anaonymise data held in BarrierTopPrioritySummary objects.
        Fields that need anonymising:
            - top_priority_summary_text
            - created_by_id
            - modified_by_id
        """
        for barrier in barriers:
            top_priority_objects = BarrierTopPrioritySummary.objects.filter(
                barrier=barrier.id
            )
            for top_priority in top_priority_objects:
                top_priority.top_priority_summary_text = Faker().paragraph(
                    nb_sentences=4
                )
                top_priority.created_by_id = self._get_dummy_user()
                top_priority.modified_by_id = self._get_dummy_user()
                top_priority.save()

    def _anonymise_valuation_assessments(self, barriers):
        """
        Function to check each type of valuation assessment and replace potentially
        sensitive data.
        Fields that need anonymising:
            - explanation (EconomicAssessment)
            - explanation (EconomicImpactAssessment)
            - explanation (ResolvabilityAssessment)
            - hmg_strategy (StrategicAssessment)
            - government_policy (StrategicAssessment)
            - trading_relations (StrategicAssessment)
            - uk_interest_and_security (StrategicAssessment)
            - uk_grants (StrategicAssessment)
            - competition (StrategicAssessment)
            - additional_information (StrategicAssessment)
        """
        for barrier in barriers:

            economic_assessments = EconomicAssessment.objects.filter(barrier=barrier.id)
            for assessment in economic_assessments:
                assessment.explanation = Faker().paragraph(nb_sentences=2)
                assessment.save()

                # Change the path of any attached documents
                for document in assessment.documents.all():
                    document.path = Faker().word() + "/" + Faker().word() + ".pdf"
                    document.save()

            economic_impact_assessments = EconomicImpactAssessment.objects.filter(
                barrier=barrier.id
            )
            for assessment in economic_impact_assessments:
                assessment.explanation = Faker().paragraph(nb_sentences=2)
                assessment.save()

            resolvability_assessments = ResolvabilityAssessment.objects.filter(
                barrier=barrier.id
            )
            for assessment in resolvability_assessments:
                assessment.explanation = Faker().paragraph(nb_sentences=2)
                assessment.save()

            strategic_assessments = StrategicAssessment.objects.filter(
                barrier=barrier.id
            )
            for assessment in strategic_assessments:
                assessment.hmg_strategy = Faker().paragraph(nb_sentences=2)
                assessment.government_policy = Faker().paragraph(nb_sentences=2)
                assessment.trading_relations = Faker().paragraph(nb_sentences=2)
                assessment.uk_interest_and_security = Faker().paragraph(nb_sentences=2)
                assessment.uk_grants = Faker().paragraph(nb_sentences=2)
                assessment.competition = Faker().paragraph(nb_sentences=2)
                assessment.additional_information = Faker().paragraph(nb_sentences=2)
                assessment.save()

    def _anonymise_wto_profiles(self, barriers):  # noqa
        """
        Function to anaonymise data held in a barriers WTO profile.
        These are all optional fields so we only need to replace ones that exist.
        Fields that need anonymising:
            - committee_notified
            - committee_notification_link
            - committee_notification_document
            - member_states
            - committee_raised_in
            - meeting_minutes
            - raised_date
            - case_number
        """
        for barrier in barriers:
            wto_profiles = WTOProfile.objects.filter(barrier=barrier.id)
            for profile in wto_profiles:
                if profile.committee_notification_link:
                    profile.committee_notification_link = (
                        "https://"
                        + Faker().word()
                        + "-"
                        + Faker().word()
                        + ".com/"
                        + Faker().word()
                    )
                if profile.case_number:
                    profile.case_number = Faker().word()

                if profile.raised_date:
                    profile.raised_date = profile.raised_date + timedelta(days=22)
                if profile.committee_notification_document:
                    for document in profile.committee_notification_document.all():
                        document.path = Faker().word() + "/" + Faker().word() + ".pdf"
                        document.save()
                if profile.meeting_minutes:
                    for document in profile.meeting_minutes.all():
                        document.path = Faker().word() + "/" + Faker().word() + ".pdf"
                        document.save()

                # Get count of countries in array
                # Loop that number of times, building array of countries by
                # randomly picking them from metadata.get_countries()
                # Overwrite existing member_states array
                if profile.member_states:
                    countries_list = get_countries()
                    number_of_states = len(profile.member_states)
                    new_country_list = []
                    i = 0
                    while i < number_of_states:
                        random_pick = random.choice(countries_list)
                        new_country_list.append(random_pick["id"])
                        i = i + 1
                    profile.member_states = new_country_list

                # Pick a random entry from the WTOCommittee table
                if profile.committee_notified:
                    wto_committee_options = WTOCommittee.objects.all()
                    random_pick = random.choice(wto_committee_options)
                    profile.committee_notified = random_pick
                if profile.committee_raised_in:
                    wto_committee_options = WTOCommittee.objects.all()
                    random_pick = random.choice(wto_committee_options)
                    profile.committee_raised_in = random_pick

                profile.save()

    def _purge_barrier_history(self, barriers):  # noqa
        """
        Function to purge all barrier histories, and their related DB objects histories.
        """
        for barrier in barriers:
            barrier.history.all().delete()
            CachedHistoryItem.objects.filter(
                barrier_id=barrier.id,
            ).delete()

            BarrierProgressUpdate.history.filter(barrier=barrier.pk).delete()
            ProgrammeFundProgressUpdate.history.filter(barrier=barrier.pk).delete()
            TeamMember.history.filter(barrier=barrier.pk).delete()
            Interaction.history.filter(barrier=barrier.pk).delete()
            EconomicAssessment.history.filter(barrier=barrier.pk).delete()
            EconomicImpactAssessment.history.filter(barrier=barrier.pk).delete()
            ResolvabilityAssessment.history.filter(barrier=barrier.pk).delete()
            StrategicAssessment.history.filter(barrier=barrier.pk).delete()
            WTOProfile.history.filter(barrier=barrier.pk).delete()
            public_barrier = PublicBarrier.objects.get(barrier=barrier.id)
            if public_barrier:
                public_barrier.history.all().delete()
                PublicBarrierNote.history.filter(
                    public_barrier=public_barrier.pk
                ).delete()

    def handle(self, *args, **options):
        logger.info("Running management command: Data Anonymise.")

        if settings.DJANGO_ENV == "prod":
            raise Exception(
                "You cannot anonymise production data. You came this close to a very bad day."
            )

        if (
            options["barrier_cutoff_date"] is None and options["barrier_id"] is None
        ) or (options["barrier_cutoff_date"] and options["barrier_id"]):
            raise Exception(
                "You have to either provide a barrier cutoff date or a single barrier ID."
            )

        if options["barrier_cutoff_date"]:
            barrier_cutoff_date_formatted = datetime.strptime(
                options["barrier_cutoff_date"], "%d-%m-%y"
            )

            logger.info(
                "Getting barriers before date: " + str(options["barrier_cutoff_date"])
            )
            barriers = Barrier.objects.filter(
                created_on__lte=barrier_cutoff_date_formatted,
            )
            logger.info("Got " + str(barriers.count()) + " barriers.")

        if options["barrier_id"]:
            logger.info("Getting barrier " + str(options["barrier_id"]))
            barriers = Barrier.objects.filter(id=options["barrier_id"])
            logger.info("Got " + str(barriers.count()) + " barrier.")

        logger.info("Anonymising barrier text fields.")
        self._anonymise_text_fields(barriers)
        logger.info("Completed anonymising text data.")

        logger.info("Anonymising barrier fields more complex than simple text fields.")
        self._anonymise_complex_barrier_fields(barriers)
        logger.info("Completed anonymising more varied & complex data fields.")

        logger.info("Randomising the date fields across barrier and sub-objects.")
        self._scramble_date_fields(barriers)
        logger.info("Completed randomising dates.")

        logger.info("Anonymising barrier user data.")
        self._anonymise_users_data(barriers)
        logger.info("Completed anonymising user data.")

        logger.info("Clearing report session data")
        self._clear_barrier_report_session_data(barriers)
        logger.info("Completed clearing report sesson data.")

        logger.info("Clearing barrier notes")
        self._clear_barrier_notes(barriers)
        logger.info("Completed removing barrier notes.")

        logger.info("Anonymising Public Barrier data.")
        self._anonymise_public_data(barriers)
        logger.info("Completed anonymising public barrier data.")

        logger.info("Anonymising Progress Update data.")
        self._anonymise_progress_updates(barriers)
        logger.info("Completed anonymising progress update data.")

        logger.info("Anonymising Next Step Items data.")
        self._anonymise_next_step_items(barriers)
        logger.info("Completed anonymising Next Step Items data.")

        logger.info("Anonymising Top Priority data.")
        self._anonymise_top_priority_data(barriers)
        logger.info("Completed anonymising Top Priority data.")

        logger.info("Anonymising valuation assessments data.")
        self._anonymise_valuation_assessments(barriers)
        logger.info("Completed anonymising valuation assessments data.")

        logger.info("Anonymising WTO profile.")
        self._anonymise_wto_profiles(barriers)
        logger.info("Completed anonymising WTO profile.")

        logger.info("Deleting barrier history")
        self._purge_barrier_history(barriers)
        logger.info("Finished deleting barrier histories.")

    # TODO:
    #
    # Date fields:
    #
    # Barrier
    # estimated_resolution_date
    # proposed_estimated_resolution_date
    # proposed_estimated_resolution_date_created
    # reported_on
    # status_date
    # priority_date
    # start_date
    #
    # Document
    # uploaded_on
    #
    # BarrierProgressUpdate
    # created_on
    # modified_on
    #
    # ProgrammeFundProgressUpdate:
    # created_on
    # modified_on
    #
    # PublicBarrier:
    # first_published_on
    # last_published_on
    # unpublished_on
    # title_updated_on
    # summary_updated_on
    #
    # BarrierNextStepItem:
    # start_date
    # completion_date
    #
    # BarrierTopPrioritySummary:
    # created_on
    # modified_on
