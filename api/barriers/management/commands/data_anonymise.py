import logging
import random
from datetime import datetime

from django.conf import settings
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
from api.interactions.models import Interaction, Mention, PublicBarrierNote

logger = logging.getLogger(__name__)


DUMMY_USER_PROFILES = [
    "3903",
    "3916",
    "3871",
    "3911",
]


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
    # ./manage.py data_anonymise --barrier_id 0454e8cb-b5e7-4a3a-91e3-b0461beb533c

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
            barrier.created_by_id = random.choice(DUMMY_USER_PROFILES)
            if barrier.modified_by_id:
                barrier.modified_by_id = random.choice(DUMMY_USER_PROFILES)
            if barrier.archived_by_id:
                barrier.archived_by_id = random.choice(DUMMY_USER_PROFILES)
            if barrier.unarchived_by_id:
                barrier.unarchived_by_id = random.choice(DUMMY_USER_PROFILES)
            if barrier.proposed_estimated_resolution_date_user_id:
                barrier.proposed_estimated_resolution_date_user_id = random.choice(
                    DUMMY_USER_PROFILES
                )

            barrier.save()

            # Change users who are listed as having a stake or
            # influence on the barrier in question.
            barrier_team_list = barrier.barrier_team.all()
            for team_member in barrier_team_list:
                team_member.id = random.choice(DUMMY_USER_PROFILES)
                team_member.save()

    def _clear_barrier_report_session_data(self, barriers):
        """
        Function to clear any data stored in the new_report_session_data
        field which could hold sensitive data which has not yet
        been committed to a completed barrier.
        """
        for barrier in barriers:
            barrier.new_report_session_data = None
            barrier.save()

    def _clear_barrier_notes(self, barriers):
        """
        Function to clear any notes attached to the barrier
        """
        for barrier in barriers:
            barrier_notes = Interaction.objects.filter(id=barrier.pk)
            for note in barrier_notes:
                note.text = Faker().paragraph(nb_sentences=4)
                note.save()

                # Documents attached to notes could have personal identifiers in the filepath.
                for document in note.documents:
                    document.path = Faker().word() + "/" + Faker().word() + ".pdf"
                    document.save()

            # Mentions attcheched to the barrier also need clearing
            barrier_mentions = Mention.objects.filter(id=barrier.pk)
            for mention in barrier_mentions:
                mention.email_used = "fake_email@fake_provider.com"
                mention.recipient = random.choice(DUMMY_USER_PROFILES)
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
                next_step_item.next_step_owner = Faker().word + " " + Faker().word
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
                top_priority.created_by_id = random.choice(DUMMY_USER_PROFILES)
                top_priority.modified_by_id = random.choice(DUMMY_USER_PROFILES)
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
                for document in economic_assessments.documents:
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

    def _purge_barrier_history(self, barriers):  # noqa
        """
        Function to purge all barrier histories.
        """
        # Barrier history
        for barrier in barriers:
            for history_item in barrier.history:
                history_item.delete()

            progress_updates = BarrierProgressUpdate.objects.filter(barrier=barrier.pk)
            for update in progress_updates:
                for history_item in update.history:
                    history_item.delete()

            programme_fund_progress_updates = BarrierProgressUpdate.objects.filter(
                barrier=barrier.pk
            )
            for update in programme_fund_progress_updates:
                for history_item in update.history:
                    history_item.delete()

            team_members = TeamMember.objects.filter(barrier=barrier.pk)
            for team_member in team_members:
                for history_item in team_member.history:
                    history_item.delete()

            notes = Interaction.objects.filter(barrier=barrier.pk)
            for note in notes:
                for history_item in note.history:
                    history_item.delete()

            economic_assessments = EconomicAssessment.objects.filter(barrier=barrier.pk)
            for assessment in economic_assessments:
                for history_item in assessment.history:
                    history_item.delete()

            economic_impact_assessments = EconomicImpactAssessment.objects.filter(
                barrier=barrier.pk
            )
            for assessment in economic_impact_assessments:
                for history_item in assessment.history:
                    history_item.delete()

            resolvability_assessments = ResolvabilityAssessment.objects.filter(
                barrier=barrier.pk
            )
            for assessment in resolvability_assessments:
                for history_item in assessment.history:
                    history_item.delete()

            strategic_assessments = StrategicAssessment.objects.filter(
                barrier=barrier.pk
            )
            for assessment in strategic_assessments:
                for history_item in assessment.history:
                    history_item.delete()

            public_barrier = PublicBarrier.objects.get(barrier=barrier.id)
            if public_barrier:
                for history_item in public_barrier.history:
                    history_item.delete()

                public_barrier_notes = PublicBarrierNote.objects.filter(
                    public_barrier=public_barrier.id
                )
                for public_note in public_barrier_notes:
                    for history_item in public_note:
                        history_item.delete()

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

        logger.info("Deleting barrier history")
        self._purge_barrier_history(barriers)
        logger.info("Finished deleting barrier histories.")
