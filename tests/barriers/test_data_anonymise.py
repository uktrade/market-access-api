import datetime
import json
import os
import uuid
from io import StringIO

from django.conf import settings
from django.core import management
from django.db import models
from django.test import TestCase, override_settings

from api.assessment.models import (
    EconomicAssessment,
    EconomicImpactAssessment,
    ResolvabilityAssessment,
    StrategicAssessment,
)
from api.barriers.management.commands.data_anonymise import Command
from api.barriers.models import (
    Barrier,
    BarrierNextStepItem,
    BarrierProgressUpdate,
    BarrierTopPrioritySummary,
    ProgrammeFundProgressUpdate,
    PublicBarrierManager,
)
from api.collaboration.models import TeamMember
from api.core.exceptions import IllegalManagementCommandException
from api.core.test_utils import APITestMixin
from api.interactions.models import Document as InteractionDocument
from api.interactions.models import Interaction, Mention, PublicBarrierNote
from api.metadata.models import BarrierTag
from api.metadata.utils import get_sectors
from api.wto.models import WTOProfile


class TestDataAnonymise(APITestMixin, TestCase):
    fixtures = [
        "barrier_priorities",
        "barrier_for_anonymisation",
        "users",
    ]

    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(
                settings.ROOT_DIR,
                "api",
                "barriers",
                "fixtures",
                "barrier_for_anonymisation.json",
            ),
            "r",
        ) as barrier_fixture:
            barrier = json.load(barrier_fixture)[0]
            cls.barrier_fields = barrier["fields"]
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.barrier = Barrier.objects.get(pk="c33dad08-b09c-4e19-ae1a-be47796a8882")
        self.barrier_queryset = Barrier.objects.all()
        # Set today's date to use as argument for management command for 'barrier_cutoff_date'
        self.today_date_object = datetime.datetime.now()
        self.today_date = self.today_date_object.strftime("%d-%m-%y")

    def _has_db_barrier_changed(self) -> bool:
        """Checks if the barrier in the database is different from the fixture.

        i.e. if the command worked or not
        """
        self.barrier.refresh_from_db()
        for key, value in self.barrier_fields.items():
            db_barrier_value = getattr(self.barrier, key)
            if isinstance(db_barrier_value, datetime.datetime):
                db_barrier_value = db_barrier_value.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            elif isinstance(db_barrier_value, datetime.date):
                db_barrier_value = db_barrier_value.strftime("%Y-%m-%d")

            elif isinstance(db_barrier_value, list):
                new_list = []
                for each in db_barrier_value:
                    if isinstance(each, uuid.UUID):
                        each = str(each)
                    new_list.append(each)
                db_barrier_value = new_list

            elif isinstance(db_barrier_value, models.Model):
                db_barrier_value = db_barrier_value.id

            elif isinstance(db_barrier_value, uuid.UUID):
                db_barrier_value = str(db_barrier_value)

            if db_barrier_value != value:
                return True
        return False

    def call_command(self, **kwargs):
        out = StringIO()
        management.call_command(
            "data_anonymise", stdout=out, stderr=StringIO(), **kwargs
        )
        self.barrier.refresh_from_db()
        return out.getvalue()

    @override_settings(DJANGO_ENV="prod")
    def test_production_run_raises_error(self):

        with self.assertRaises(IllegalManagementCommandException):
            self.call_command(barrier_cutoff_date=self.today_date)

        assert not self._has_db_barrier_changed()

    def test_dry_run(self):
        output = self.call_command(barrier_cutoff_date=self.today_date, dry_run=True)
        assert not self._has_db_barrier_changed()
        assert "Running in dry run mode" in output
        assert "Anonymisation complete, rolling back changes" in output

    def test_live_run(self):
        output = self.call_command(barrier_cutoff_date=self.today_date, dry_run=False)
        assert self._has_db_barrier_changed()
        assert (
            "Running in live run mode. Changes will be committed to the database"
            in output
        )

    def test_logging(self):
        output = self.call_command(barrier_cutoff_date=self.today_date, dry_run=False)
        assert "Starting anonymising barrier data" in output
        assert "Finished anonymising barrier data" in output

    def test_anonymise_text_fields(self):
        Command.anonymise_text_fields(self.barrier_queryset)
        self.barrier.refresh_from_db()
        assert self.barrier.title != self.barrier_fields["title"]
        assert self.barrier.summary != self.barrier_fields["summary"]
        assert (
            self.barrier.archived_explanation
            != self.barrier_fields["archived_explanation"]
        )
        assert (
            self.barrier.next_steps_summary != self.barrier_fields["next_steps_summary"]
        )
        assert self.barrier.archived_reason != self.barrier_fields["archived_reason"]
        assert (
            self.barrier.unarchived_reason != self.barrier_fields["unarchived_reason"]
        )
        assert (
            self.barrier.public_eligibility_summary
            != self.barrier_fields["public_eligibility_summary"]
        )
        assert (
            self.barrier.economic_assessment_eligibility_summary
            != self.barrier_fields["economic_assessment_eligibility_summary"]
        )
        assert (
            self.barrier.commercial_value_explanation
            != self.barrier_fields["commercial_value_explanation"]
        )
        assert (
            self.barrier.top_priority_rejection_summary
            != self.barrier_fields["top_priority_rejection_summary"]
        )
        assert (
            self.barrier.estimated_resolution_date_change_reason
            != self.barrier_fields["estimated_resolution_date_change_reason"]
        )
        assert (
            self.barrier.export_description != self.barrier_fields["export_description"]
        )

    def test_anonymise_complex_fields(self):
        Command.anonymise_complex_barrier_fields(self.barrier_queryset)
        self.barrier.refresh_from_db()
        assert self.barrier.companies[0] != self.barrier_fields["companies"][0]
        assert self.barrier.companies[0]["name"].endswith(
            (" CO.", " PLC.", " LTD.", " INC.")
        )

        assert (
            self.barrier.related_organisations[0]
            != self.barrier_fields["related_organisations"][0]
        )
        assert self.barrier.related_organisations[0]["name"].endswith(
            (" CO.", " PLC.", " LTD.", " INC.")
        )

        assert self.barrier.commercial_value != self.barrier_fields["commercial_value"]

        sectors_list = [each["id"] for each in get_sectors()]
        for each in self.barrier.sectors:
            assert str(each) in sectors_list
        assert len(self.barrier.sectors) == len(self.barrier_fields["sectors"])

        assert str(self.barrier.main_sector) != self.barrier_fields["main_sector"]
        assert self.barrier.main_sector not in self.barrier.sectors

        assert len(self.barrier.organisations.all()) == 0

    def test_anonymise_tags(self):
        self.barrier.tags.add(BarrierTag.objects.first())
        Command.anonymise_complex_barrier_fields(self.barrier_queryset)
        self.barrier.refresh_from_db()
        assert len(self.barrier.tags.all()) == 1

    def test_anonymise_date_fields(self):
        Command.scramble_barrier_date_fields(self.barrier_queryset)
        self.barrier.refresh_from_db()
        assert (
            self.barrier.estimated_resolution_date
            != self.barrier_fields["estimated_resolution_date"]
        )
        assert (
            self.barrier.proposed_estimated_resolution_date
            != self.barrier_fields["proposed_estimated_resolution_date"]
        )
        assert (
            self.barrier.proposed_estimated_resolution_date_created
            != self.barrier_fields["proposed_estimated_resolution_date_created"]
        )
        assert self.barrier.reported_on != self.barrier_fields["reported_on"]
        assert self.barrier.status_date != self.barrier_fields["status_date"]
        assert self.barrier.priority_date != self.barrier_fields["priority_date"]
        assert self.barrier.start_date != self.barrier_fields["start_date"]

    def test_anonymise_user_data(self):
        Command.anonymise_users_data(self.barrier_queryset)
        self.barrier.refresh_from_db()
        assert self.barrier.created_by_id != self.user.id
        assert self.barrier.modified_by_id != self.user.id
        assert self.barrier.archived_by_id != self.user.id
        assert self.barrier.unarchived_by_id != self.user.id
        assert self.barrier.proposed_estimated_resolution_date_user_id != self.user.id

    def test_anonymise_barrier_team(self):
        tm = TeamMember.objects.create(
            barrier=self.barrier, user=self.user, created_by=self.user
        )
        self.barrier.barrier_team.add(tm)
        Command.anonymise_users_data(self.barrier_queryset)
        self.barrier.refresh_from_db()
        assert self.user not in self.barrier.barrier_team.all()
        assert self.barrier.barrier_team.count() == 1
        assert self.barrier.barrier_team.first().created_by_id != self.user.id

    def test_clear_barrier_report_session_data(self):
        Command.clear_barrier_report_session_data(self.barrier_queryset)
        self.barrier.refresh_from_db()
        assert not self.barrier.new_report_session_data

    def test_clear_barrier_notes(self):
        note = Interaction.objects.create(
            barrier=self.barrier,
            kind="Comment",
            text="Test note",
            created_by=self.user,
            modified_by=self.user,
        )
        document = InteractionDocument.objects.create(
            original_filename="test.jpg",
            size=1337,
        )
        note.documents.add(document)

        Command.anonymise_barrier_notes(self.barrier_queryset)
        note.refresh_from_db()
        document.refresh_from_db()
        assert note.text != "Test note"
        assert note.created_by_id != self.user.id
        assert note.modified_by_id != self.user.id
        assert document.original_filename != "test.jpg"
        assert "test.jpg" not in document.document.path
        assert document.document.uploaded_on != self.today_date_object

    def test_anonymise_barrier_mentions(self):
        mention = Mention.objects.create(
            barrier=self.barrier,
            recipient=self.user,
            email_used=self.user.email,
            text="test",
        )
        Command.anonymise_barrier_notes(self.barrier_queryset)
        mention.refresh_from_db()
        assert mention.recipient_id != self.user.id
        assert mention.email_used != self.user.email
        assert mention.text != "test"

    def test_delete_public_barrier(self):
        public_barrier, _ = PublicBarrierManager.get_or_create_for_barrier(self.barrier)
        note = PublicBarrierNote.objects.create(
            public_barrier=public_barrier, text="test", created_by=self.user
        )
        Command.anonymise_public_data(self.barrier_queryset)
        public_barrier.refresh_from_db()
        note.refresh_from_db()
        assert public_barrier.title != self.barrier_fields["title"]
        assert public_barrier.summary != self.barrier_fields["summary"]
        assert public_barrier.internal_title_at_update != self.barrier_fields["title"]
        assert (
            public_barrier.internal_summary_at_update != self.barrier_fields["summary"]
        )
        assert public_barrier._public_view_status == 0
        assert note.text != "test"

    def test_anonymise_progress_updates(self):
        bpu = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status="ON_TRACK",
            update="update",
            next_steps="next steps",
        )
        pfpu = ProgrammeFundProgressUpdate.objects.create(
            barrier=self.barrier,
            milestones_and_deliverables="milestones and deliverables",
            expenditure="expenditure",
        )
        Command.anonymise_progress_updates(self.barrier_queryset)
        bpu.refresh_from_db()
        pfpu.refresh_from_db()

        assert bpu.update != "update"
        assert bpu.next_steps != "next steps"
        assert pfpu.milestones_and_deliverables != "milestones and deliverables"
        assert pfpu.expenditure != "expenditure"

    def test_anonymise_next_steps(self):
        bnsi = BarrierNextStepItem.objects.create(
            barrier=self.barrier,
            next_step_owner="john",
            next_step_item="item",
            completion_date=self.today_date_object,
        )
        original_start_date = bnsi.start_date
        Command.anonymise_next_step_items(self.barrier_queryset)
        bnsi.refresh_from_db()
        assert bnsi.next_step_owner != "john"
        assert bnsi.next_step_item != "item"
        assert bnsi.completion_date != self.today_date_object
        assert bnsi.start_date != original_start_date

    def test_anonymise_top_priority_data(self):
        btps = BarrierTopPrioritySummary.objects.create(
            barrier=self.barrier,
            top_priority_summary_text="test",
            modified_by=self.user,
            created_on=self.today_date_object,
            modified_on=self.today_date_object,
            created_by=self.user,
        )
        Command.anonymise_top_priority_data(self.barrier_queryset)
        btps.refresh_from_db()
        assert btps.top_priority_summary_text != "test"
        assert btps.modified_by_id != self.user.id
        assert btps.created_on != self.today_date
        assert btps.modified_on != self.today_date

    def test_anonymise_valuation_assessments(self):
        ea = EconomicAssessment.objects.create(
            barrier=self.barrier,
            explanation="test",
        )
        eia = EconomicImpactAssessment.objects.create(
            economic_assessment=ea, barrier=self.barrier, explanation="test", impact=1
        )
        ra = ResolvabilityAssessment.objects.create(
            barrier=self.barrier,
            explanation="test",
            time_to_resolve=0,
            effort_to_resolve=0,
        )
        sa = StrategicAssessment.objects.create(
            barrier=self.barrier,
            hmg_strategy="hmg_strategy",
            government_policy="government_policy",
            trading_relations="trading_relations",
            uk_interest_and_security="uk_interest_and_security",
            uk_grants="uk_grants",
            competition="competition",
            additional_information="additional_information",
            scale=1,
        )
        Command.anonymise_valuation_assessments(self.barrier_queryset)
        ea.refresh_from_db()
        eia.refresh_from_db()
        ra.refresh_from_db()
        sa.refresh_from_db()

        assert ea.explanation != "test"
        assert eia.explanation != "test"
        assert ra.explanation != "test"
        assert sa.hmg_strategy != "hmg_strategy"
        assert sa.government_policy != "government_policy"
        assert sa.trading_relations != "trading_relations"
        assert sa.uk_interest_and_security != "uk_interest_and_security"
        assert sa.uk_grants != "uk_grants"
        assert sa.competition != "competition"
        assert sa.additional_information != "additional_information"

    def test_anonymise_wto_profiles(self):
        member_state_id = uuid.uuid4()
        wto = WTOProfile.objects.create(
            barrier=self.barrier,
            committee_notification_link="https://www.example.com",
            case_number="1234",
            raised_date=self.today_date_object,
            member_states=[
                member_state_id,
            ],
            wto_has_been_notified=True,
        )
        Command.anonymise_wto_profiles(self.barrier_queryset)
        wto.refresh_from_db()
        assert wto.committee_notification_link != "https://www.example.com"
        assert "https://" in wto.committee_notification_link
        assert wto.case_number != "1234"
        assert wto.raised_date != self.today_date
        assert len(wto.member_states) == 1
        assert wto.member_states[0] != member_state_id
