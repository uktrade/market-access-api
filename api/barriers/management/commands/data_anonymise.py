import logging
import random
import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand
from django.db import transaction
from django.db.models import signals
from factory.django import mute_signals
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
    User,
)
from api.collaboration.models import TeamMember
from api.core.exceptions import (
    AtomicTransactionException,
    IllegalManagementCommandException,
)
from api.interactions.models import Interaction, PublicBarrierNote
from api.metadata.models import BarrierTag, Organisation
from api.metadata.utils import get_countries, get_sectors
from api.wto.models import WTOCommittee, WTOProfile

logger = logging.getLogger(__name__)

SAFE_ENVIRONMENTS = [
    "uat",
    "local",
    "dev",
    "test",
]  # the environments we can run this command on


def _get_dummy_user():
    # Development environments can use placeholder IDs that exist on those DBs
    # local will need to source a random user from the local DB
    if settings.DJANGO_ENV == "local":
        AuthUser = get_user_model()
        user_list = AuthUser.objects.all()
        random_pick = random.choice(user_list)
        return random_pick.id
    elif settings.DJANGO_ENV == "test":
        # if we're testing, we want to assign a different user to the one defined in
        # the test fixtures, so we can test that the user has been changed.
        AuthUser = get_user_model()
        user, _ = AuthUser.objects.get_or_create(
            username="test@example.com",
            email="test@example.com",
        )
        return user.id
    else:
        # if we're on a non-local environment, we want to assign a random user from a
        # pre-defined list. These are the administrator emails.
        from django.core.cache import cache

        if cache.get("admin_users"):
            admin_users = cache.get("admin_users")
        else:
            admin_users = User.objects.filter(groups__name="Administrator")
            cache.set("admin_users", admin_users)

        return random.choice(admin_users).id


def _randomise_date(date):
    """
    Function to take a date and add or minus days to mask the actual date.
    """
    if date:
        days_change = random.randint(1, 100)
        days_change = days_change * -1
        return date + timedelta(days=days_change)
    return None


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

    # ./manage.py data_anonymise --barrier_cutoff_date 01-01-24
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

        parser.add_argument(
            "--dry_run",
            type=bool,
            help="Run the command without committing any changes to the DB.",
            default=False,
            nargs="?",
        )

    @staticmethod
    def anonymise_text_fields(barriers):  # noqa
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
            if barrier.next_steps_summary:
                barrier.next_steps_summary = Faker().paragraph(nb_sentences=2)
            if barrier.archived_reason:
                barrier.archived_reason = Faker().word()
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

    @staticmethod
    def anonymise_complex_barrier_fields(barriers):  # noqa
        """
        Function to take fields more complex than a text field and either
        scramble or anonymise their contents.
        Fields that will be anonymised (if they have existing value):
            - companies
            - related_organisations
            - commercial_value
            - sectors
            - main_sector
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

            new_sectors_list = []
            top_level_sectors = [
                sector for sector in get_sectors() if sector["level"] == 0
            ]
            if barrier.sectors:
                number_of_sectors = len(barrier.sectors)
                i = 0
                while i < number_of_sectors:
                    random_pick = random.choice(top_level_sectors)
                    new_sectors_list.append(random_pick["id"])
                    i = i + 1
                barrier.sectors = new_sectors_list

            if barrier.main_sector:
                random_pick = random.choice(top_level_sectors)
                main_sector_updated = False
                while main_sector_updated is not True:
                    # Cannot have a main_sector that is in the other sectors list
                    if random_pick["id"] not in new_sectors_list:
                        barrier.main_sector = random_pick["id"]
                        main_sector_updated = True
                    else:
                        random_pick = random.choice(top_level_sectors)

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

    @staticmethod
    def scramble_barrier_date_fields(barriers):
        """
        Function to scramble date fields of barrier and child objects
        """
        for barrier in barriers:
            barrier.estimated_resolution_date = _randomise_date(
                barrier.estimated_resolution_date
            )
            barrier.proposed_estimated_resolution_date = _randomise_date(
                barrier.proposed_estimated_resolution_date
            )
            barrier.proposed_estimated_resolution_date_created = _randomise_date(
                barrier.proposed_estimated_resolution_date_created
            )
            barrier.reported_on = _randomise_date(barrier.reported_on)
            barrier.status_date = _randomise_date(barrier.status_date)
            barrier.priority_date = _randomise_date(barrier.priority_date)
            barrier.start_date = _randomise_date(barrier.start_date)

            barrier.save()

    @staticmethod
    def anonymise_users_data(barriers):
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
            barrier.created_by_id = _get_dummy_user()
            if barrier.modified_by_id:
                barrier.modified_by_id = _get_dummy_user()
            if barrier.archived_by_id:
                barrier.archived_by_id = _get_dummy_user()
            if barrier.unarchived_by_id:
                barrier.unarchived_by_id = _get_dummy_user()
            if barrier.proposed_estimated_resolution_date_user_id:
                barrier.proposed_estimated_resolution_date_user_id = _get_dummy_user()

            barrier.save()

            # Change users who are listed as having a stake or
            # influence on the barrier in question.
            barrier_team_list = barrier.barrier_team.all()
            for team_member in barrier_team_list:
                new_member_id = _get_dummy_user()
                TeamMember.objects.filter(id=team_member.id).update(
                    user=new_member_id,
                    created_by_id=new_member_id,
                    modified_by_id=new_member_id,
                )

    @staticmethod
    def clear_barrier_report_session_data(barriers):
        """
        Function to clear any data stored in the new_report_session_data
        field which could hold sensitive data which has not yet
        been committed to a completed barrier.
        """
        for barrier in barriers:
            barrier.new_report_session_data = ""
            barrier.save()

    @staticmethod
    def anonymise_barrier_notes(barriers):
        """
        Function to clear any notes attached to the barrier
        """
        for barrier in barriers:
            barrier_notes = Interaction.objects.filter(barrier=barrier.pk)

            for note in barrier_notes:
                note.text = Faker().paragraph(nb_sentences=4)
                AuthUser = get_user_model()
                note_user = AuthUser.objects.get(id=_get_dummy_user())
                note.created_by = note_user
                note.modified_by = note_user
                note.save()

                # Documents attached to notes could have personal identifiers in the filepath.
                for document in note.documents.all():
                    mock_filename = (
                        f"{Faker().word()}-{Faker().word()}-{uuid.uuid4()}.pdf"
                    )
                    document.original_filename = mock_filename
                    document.document.path = f"documents/2023-01-01/{mock_filename}"
                    document.document.uploaded_on = _randomise_date(
                        document.document.uploaded_on
                    )
                    document.save()
                    document.document.save()

            # Mentions attached to the barrier also need clearing
            for mention in barrier.mention.all():
                mention.email_used = "fake_email@fake_provider.com"
                mention.recipient_id = _get_dummy_user()
                mention.text = Faker().paragraph(nb_sentences=1)

                mention.save()

    @staticmethod
    def anonymise_public_data(barriers):
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

                # anonymising the dates
                public_barrier.first_published_on = _randomise_date(
                    public_barrier.first_published_on
                )
                public_barrier.last_published_on = _randomise_date(
                    public_barrier.last_published_on
                )
                public_barrier.unpublished_on = _randomise_date(
                    public_barrier.unpublished_on
                )
                public_barrier.title_updated_on = _randomise_date(
                    public_barrier.title_updated_on
                )
                public_barrier.summary_updated_on = _randomise_date(
                    public_barrier.summary_updated_on
                )

                # Save the public barrier
                public_barrier.save()

                # Find all the public barrier notes and clear the text therein
                public_barrier_notes = PublicBarrierNote.objects.filter(
                    public_barrier=public_barrier.id
                )
                for public_note in public_barrier_notes:
                    public_note.text = Faker().paragraph(nb_sentences=4)
                    public_note.save(trigger_mentions=False)

                public_barrier = PublicBarrier.objects.get(barrier=barrier.id)

    @staticmethod
    def anonymise_progress_updates(barriers):
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
                update.created_on = _randomise_date(update.created_on)
                update.modified_on = _randomise_date(update.modified_on)
                update.save()

            programme_fund_progress_updates = (
                ProgrammeFundProgressUpdate.objects.filter(barrier=barrier.id)
            )
            for update in programme_fund_progress_updates:
                update.milestones_and_deliverables = Faker().paragraph(nb_sentences=4)
                update.expenditure = Faker().paragraph(nb_sentences=4)
                update.created_on = _randomise_date(update.created_on)
                update.modified_on = _randomise_date(update.modified_on)
                update.save()

    @staticmethod
    def anonymise_next_step_items(barriers):
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
                next_step_item.start_date = _randomise_date(next_step_item.start_date)
                next_step_item.completion_date = _randomise_date(
                    next_step_item.completion_date
                )
                next_step_item.save()

    @staticmethod
    def anonymise_top_priority_data(barriers):
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
                top_priority.created_by_id = _get_dummy_user()
                top_priority.modified_by_id = _get_dummy_user()
                top_priority.created_on = _randomise_date(top_priority.created_on)
                top_priority.modified_on = _randomise_date(top_priority.modified_on)
                top_priority.save()

    @staticmethod
    def anonymise_valuation_assessments(barriers):
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
                    document.path = (
                        Faker().word()
                        + "/"
                        + str(uuid.uuid4())
                        + "/"
                        + Faker().word()
                        + ".pdf"
                    )
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

    @staticmethod
    def anonymise_wto_profiles(barriers):  # noqa
        """
        Function to anonymise data held in a barriers WTO profile.
        These are all optional fields, so we only need to replace ones that exist.
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

                profile.raised_date = _randomise_date(profile.raised_date)
                if profile.committee_notification_document:
                    path = f"{Faker().word()}/{Faker().word()}/{uuid.uuid4()}.pdf"
                    profile.committee_notification_document.path = path
                    profile.committee_notification_document.save()
                if profile.meeting_minutes:
                    path = f"{Faker().word()}/{Faker().word()}/{uuid.uuid4()}.pdf"
                    profile.meeting_minutes.path = path
                    profile.meeting_minutes.save()

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

    def handle(self, *args, **options):
        self.stdout.write("Running management command: Data Anonymise.")

        if settings.DJANGO_ENV not in SAFE_ENVIRONMENTS:
            raise IllegalManagementCommandException(
                "You cannot anonymise data outside of UAT, Dev, or local. You came this close to a very bad day."
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

            self.stdout.write(
                "Getting barriers before date: " + str(options["barrier_cutoff_date"])
            )
            barriers = Barrier.objects.filter(
                created_on__lte=barrier_cutoff_date_formatted,
            )
            self.stdout.write("Got " + str(barriers.count()) + " barriers.")

        if options["barrier_id"]:
            self.stdout.write("Getting barrier " + str(options["barrier_id"]))
            barriers = Barrier.objects.filter(id=options["barrier_id"])
            self.stdout.write("Got " + str(barriers.count()) + " barrier.")

        if options.get("dry_run", False):
            try:
                with transaction.atomic():
                    self.stdout.write("Running in dry run mode.")
                    self.anonymise(barriers)
                    raise AtomicTransactionException()
            except AtomicTransactionException:
                self.stdout.write("Anonymisation complete, rolling back changes")
        else:
            self.stdout.write(
                "Running in live run mode. Changes will be committed to the database"
            )
            self.anonymise(barriers)

    @mute_signals(signals.pre_save, signals.post_save, signals.m2m_changed)
    def anonymise(self, barriers):
        self.stdout.write("Starting anonymising barrier data.")

        # disabling signals so GOV.NOTIFY isn't called as part of a post_save signal
        self.stdout.write("Randomising the date fields across barrier and sub-objects.")
        self.scramble_barrier_date_fields(barriers)
        self.stdout.write("Completed randomising dates.")

        self.stdout.write("Anonymising barrier text fields.")
        self.anonymise_text_fields(barriers)
        self.stdout.write("Completed anonymising text data.")

        self.stdout.write(
            "Anonymising barrier fields more complex than simple text fields."
        )
        self.anonymise_complex_barrier_fields(barriers)
        self.stdout.write("Completed anonymising more varied & complex data fields.")

        self.stdout.write("Anonymising barrier user data.")
        self.anonymise_users_data(barriers)
        self.stdout.write("Completed anonymising user data.")

        self.stdout.write("Clearing report session data")
        self.clear_barrier_report_session_data(barriers)
        self.stdout.write("Completed clearing report session data.")

        self.stdout.write("Clearing barrier notes")
        self.anonymise_barrier_notes(barriers)
        self.stdout.write("Completed removing barrier notes.")

        self.stdout.write("Anonymising Public Barrier data.")
        self.anonymise_public_data(barriers)
        self.stdout.write("Completed anonymising public barrier data.")

        self.stdout.write("Anonymising Progress Update data.")
        self.anonymise_progress_updates(barriers)
        self.stdout.write("Completed anonymising progress update data.")

        self.stdout.write("Anonymising Next Step Items data.")
        self.anonymise_next_step_items(barriers)
        self.stdout.write("Completed anonymising Next Step Items data.")

        self.stdout.write("Anonymising Top Priority data.")
        self.anonymise_top_priority_data(barriers)
        self.stdout.write("Completed anonymising Top Priority data.")

        self.stdout.write("Anonymising valuation assessments data.")
        self.anonymise_valuation_assessments(barriers)
        self.stdout.write("Completed anonymising valuation assessments data.")

        self.stdout.write("Anonymising WTO profile.")
        self.anonymise_wto_profiles(barriers)
        self.stdout.write("Completed anonymising WTO profile.")

        # DEVELOPER NOTE #
        # This script needs a final step to anonymise historical barrier data
        # as this information would be visible on the history tab. We originally
        # deleted the history instead, but this caused multiple testing
        # errors across various areas of the application that require some history
        # items to exist. If this script is to be used as a data anonymiser
        # again, this will need to be implemented. As an extension to create_mock_barriers
        # leaving history intact is safe.
        # DEVELOPER NOTE #

        self.stdout.write("Finished anonymising barrier data.")
