from datetime import datetime, timedelta, timezone
from logging import getLogger

import dateutil.parser
import freezegun
from django.contrib.auth.models import Group
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.barriers.models import BarrierNextStepItem, BarrierProgressUpdate
from api.collaboration.models import TeamMember
from api.core.test_utils import APITestMixin, create_test_user
from api.interactions.models import Interaction, Mention
from api.metadata.constants import (
    NEXT_STEPS_ITEMS_STATUS_CHOICES,
    PROGRESS_UPDATE_CHOICES,
    BarrierStatus,
    PublicBarrierStatus,
)
from api.metadata.models import BarrierTag, ExportType, Organisation
from tests.barriers.factories import BarrierFactory
from tests.history.factories import ProgrammeFundProgressUpdateFactory

logger = getLogger(__name__)


freezegun.configure(extend_ignore_list=["transformers"])


class TestDashboardTasksView(APITestMixin, APITestCase):
    """Test cases for the Dashboard tasks list retrieval"""

    def setUp(self):
        super().setUp()

        """ Create test users, the basic URL and governement orgs used in all tests"""

        self.request_url = reverse("get-dashboard-tasks")
        self.test_user = create_test_user(
            first_name="Testo",
            last_name="Useri",
            email="Testo@Useri.com",
            username="TestoUseri",
        )
        self.test_user_2 = create_test_user(
            first_name="Testduo",
            last_name="Userii",
            email="Testduo@Userii.com",
            username="TestduoUserii",
        )
        self.test_government_departments = Organisation.objects.all()[:2]

    def basic_barrier_setUp(self, erd_time=None):
        """Create basic barrier with an estimated resolution date used in majority of tests"""
        if erd_time == "future":
            erd = datetime.now() + timedelta(days=200)
        elif erd_time == "past":
            erd = datetime.now() - timedelta(days=400)
        else:
            erd = None
        self.barrier = BarrierFactory(
            estimated_resolution_date=erd,
        )
        self.barrier.organisations.add(*self.test_government_departments)

    def owner_user_setUp(self):
        """Add user to barrier team"""
        tm = TeamMember.objects.create(
            barrier=self.barrier,
            user=self.test_user,
            created_by=self.test_user,
            role="Owner",
        )
        self.barrier.barrier_team.add(tm)

    def public_barrier_setUp(self):
        """Setup method for tasks requiring public barrier data"""
        api_client = self.create_api_client(user=self.test_user)
        # Create a public barrier with only a title that wont trigger other tasks
        self.barrier = BarrierFactory(
            estimated_resolution_date=datetime.now() + timedelta(days=500),
        )
        self.barrier.organisations.add(*self.test_government_departments)
        allowed_to_publish_url = reverse(
            "public-barriers-allow-for-publishing-process",
            kwargs={"pk": self.barrier.id},
        )
        self.barrier.public_barrier.title = "adding a title"
        self.barrier.public_barrier.save()
        api_client.post(allowed_to_publish_url, format="json", data={})
        self.barrier.refresh_from_db()

        # Create a public barrier with only a summary that wont trigger other tasks
        self.barrier_2 = BarrierFactory(
            estimated_resolution_date=datetime.now() + timedelta(days=500),
        )
        self.barrier_2.organisations.add(*self.test_government_departments)
        allowed_to_publish_url = reverse(
            "public-barriers-allow-for-publishing-process",
            kwargs={"pk": self.barrier_2.id},
        )
        self.barrier_2.public_barrier.summary = "adding a summary"
        self.barrier_2.public_barrier.save()
        api_client.post(allowed_to_publish_url, format="json", data={})
        self.barrier_2.refresh_from_db()

        # Attach test_user as the owner to the barriers
        tm = TeamMember.objects.create(
            barrier=self.barrier,
            user=self.test_user,
            created_by=self.test_user,
            role="Owner",
        )
        self.barrier.barrier_team.add(tm)
        tm_2 = TeamMember.objects.create(
            barrier=self.barrier_2,
            user=self.test_user,
            created_by=self.test_user,
            role="Owner",
        )
        self.barrier_2.barrier_team.add(tm_2)

        # Attach test_user_2 as a contributor to the barriers
        tm = TeamMember.objects.create(
            barrier=self.barrier, user=self.test_user_2, created_by=self.test_user_2
        )
        self.barrier.barrier_team.add(tm)
        tm_2 = TeamMember.objects.create(
            barrier=self.barrier_2, user=self.test_user_2, created_by=self.test_user_2
        )
        self.barrier_2.barrier_team.add(tm_2)

    def test_user_with_no_barriers(self):
        """Users need to be part of a barrier team to retrieve a task list
        This test will expect an empty set of response data."""
        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_publishing_task_editor_user_info_required_not_owner(self):
        """Members of the barrier team do not get tasks related to publishing.
        Expect no tasks returned"""

        self.public_barrier_setUp()

        api_client = self.create_api_client(user=self.test_user_2)
        response = api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_publishing_task_editor_user_info_required(self):
        """Owners of the barrier need to enter a public title and public summary.
        If either of these fields are missing, we generate a task."""

        self.public_barrier_setUp()

        self.barrier.public_barrier.set_to_allowed_date = datetime.now()
        self.barrier.public_barrier.save()

        expected_deadline = dateutil.parser.parse(
            self.barrier.public_barrier.set_to_allowed_date.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline = expected_deadline.strftime("%d %B %Y")

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 2
        for barrier in response.data["results"]:
            assert len(barrier["task_list"]) == 1
            assert barrier["task_list"][0]["tag"] == "PUBLICATION REVIEW"
            assert (
                "Add a public title and summary" in barrier["task_list"][0]["message"]
            )
            # Check countdown has been substituted into message
            assert (
                f"This needs to be done by {expected_deadline}."
                in barrier["task_list"][0]["message"]
            )

    def test_publishing_task_editor_user_send_to_approval(self):
        """A second type of task is added in place of the missing information
        task if both title and summary are filled in requesting the user to send
        the barrier to an approver."""

        self.public_barrier_setUp()

        # Add summary to barrier with only a title
        self.barrier.public_barrier.summary = "adding a summary"
        self.barrier.public_barrier.set_to_allowed_date = datetime.now()
        self.barrier.public_barrier.save()

        expected_deadline = dateutil.parser.parse(
            self.barrier.public_barrier.set_to_allowed_date.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline = expected_deadline.strftime("%d %B %Y")

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 2

        # Count the expected task types
        missing_info_task_count = 0
        submit_task_count = 0
        for barrier in response.data["results"]:
            assert barrier["task_list"][0]["tag"] == "PUBLICATION REVIEW"
            # Message will be different for barrier with both title and sumary, but we
            # also expect for one of the tasks to be the previously tested message
            if (
                "Submit for clearance checks and GOV.UK publication approval"
                in barrier["task_list"][0]["message"]
            ):
                submit_task_count = submit_task_count + 1
                # Check countdown has been substituted into message
                assert f"by {expected_deadline}." in barrier["task_list"][0]["message"]
            elif "Add a public title and summary" in barrier["task_list"][0]["message"]:
                missing_info_task_count = missing_info_task_count + 1
                # Check countdown has been substituted into message
                assert (
                    f"This needs to be done by {expected_deadline}."
                    in barrier["task_list"][0]["message"]
                )

        assert submit_task_count == 1
        assert missing_info_task_count == 1

    def test_publishing_task_editor_user_send_to_approval_overdue(self):
        """This task needs to be completed within a timeframe tracked
        on the public barrier. The dashboard task has a seperate tag
        for when this countdown is passed."""

        self.public_barrier_setUp()

        # Add summary to barrier with only a title
        self.barrier.public_barrier.summary = "adding a summary"
        self.barrier.public_barrier.save()

        # Modify the public barrier missing the title to be overdue by
        # making set_to_allowed_on more than 30 days in the past
        self.barrier.public_barrier.set_to_allowed_on = datetime.now() - timedelta(
            days=40
        )
        self.barrier.public_barrier.save()

        # Modify the public barrier missing the summary to be overdue by
        # making set_to_allowed_on more than 30 days in the past
        self.barrier_2.public_barrier.set_to_allowed_on = datetime.now() - timedelta(
            days=40
        )
        self.barrier_2.public_barrier.save()

        expected_deadline_1 = dateutil.parser.parse(
            self.barrier.public_barrier.set_to_allowed_on.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline_1 = expected_deadline_1.strftime("%d %B %Y")

        expected_deadline_2 = dateutil.parser.parse(
            self.barrier_2.public_barrier.set_to_allowed_on.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline_2 = expected_deadline_2.strftime("%d %B %Y")

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 2

        # Count the expected task types
        missing_info_task_count = 0
        submit_task_count = 0
        for barrier in response.data["results"]:
            assert barrier["task_list"][0]["tag"] == "OVERDUE REVIEW"
            # Message will be different for barrier with both title and sumary, but we
            # also expect for one of the tasks to be the previously tested message
            if (
                "Submit for clearance checks and GOV.UK publication approval"
                in barrier["task_list"][0]["message"]
            ):
                submit_task_count = submit_task_count + 1
                # Check countdown has been substituted into message
                assert (
                    f"by {expected_deadline_1}." in barrier["task_list"][0]["message"]
                )
            elif "Add a public title and summary" in barrier["task_list"][0]["message"]:
                missing_info_task_count = missing_info_task_count + 1
                # Check countdown has been substituted into message
                assert (
                    f"This needs to be done by {expected_deadline_2}."
                    in barrier["task_list"][0]["message"]
                )

        assert submit_task_count == 1
        assert missing_info_task_count == 1

    def test_publishing_task_approver_user_approve_request(self):
        """This task is for users with approver permissions only. We need
        to check that the task is added when the barrier is in a specific status"""

        self.public_barrier_setUp()

        # Set barrier to AWAITING_APPROVAL status and give it both title and summary
        self.barrier.public_barrier.public_view_status = (
            PublicBarrierStatus.APPROVAL_PENDING
        )
        self.barrier.public_barrier.summary = "adding a summary"
        self.barrier.public_barrier.save()

        # Update user to have the approver permission
        self.test_user.groups.add(Group.objects.get(name="Public barrier approver"))
        self.test_user.save()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 2

        # Count the expected task types
        for result_barrier in response.data["results"]:
            if result_barrier["barrier_id"] == self.barrier.id:
                assert result_barrier["task_list"][0]["tag"] == "PUBLICATION REVIEW"
                assert (
                    "Approve this barrier" in result_barrier["task_list"][0]["message"]
                )

    def test_publishing_task_approver_user_approve_request_no_permission(self):
        """This task is for users with approver permissions only. We need
        to check that the task is not added when the user is only an editor."""

        self.public_barrier_setUp()

        # Set barrier to AWAITING_APPROVAL status and give it both title and summary
        self.barrier.public_barrier.public_view_status = (
            PublicBarrierStatus.APPROVAL_PENDING
        )
        self.barrier.public_barrier.summary = "adding a summary"
        self.barrier.public_barrier.set_to_allowed_date = datetime.now()
        self.barrier.public_barrier.save()

        expected_deadline = dateutil.parser.parse(
            self.barrier.public_barrier.set_to_allowed_date.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline = expected_deadline.strftime("%d %B %Y")

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 1
        for barrier in response.data["results"]:
            assert len(barrier["task_list"]) == 1
            assert barrier["task_list"][0]["tag"] == "PUBLICATION REVIEW"
            assert (
                "Add a public title and summary" in barrier["task_list"][0]["message"]
            )
            # Check countdown has been substituted into message
            assert (
                f"This needs to be done by {expected_deadline}."
                in barrier["task_list"][0]["message"]
            )

    def test_publishing_task_approver_user_approve_request_overdue(self):
        """This task needs to be completed within a timeframe tracked
        on the public barrier. The dashboard task has a seperate tag
        for when this countdown is passed."""

        self.public_barrier_setUp()

        # Set barrier to AWAITING_APPROVAL status and give it both title and summary
        self.barrier.public_barrier.public_view_status = (
            PublicBarrierStatus.APPROVAL_PENDING
        )
        self.barrier.public_barrier.summary = "adding a summary"
        self.barrier.public_barrier.save()

        # Modify the public barrier missing the title to be overdue by making
        # set_to_allowed_on more than 30 days in the past
        self.barrier.public_barrier.set_to_allowed_on = datetime.now() - timedelta(
            days=40
        )
        self.barrier.public_barrier.save()

        # Modify the public barrier missing the summary to be overdue by
        # making set_to_allowed_on more than 30 days in the past
        self.barrier_2.public_barrier.set_to_allowed_on = datetime.now() - timedelta(
            days=40
        )
        self.barrier_2.public_barrier.save()

        expected_deadline_1 = dateutil.parser.parse(
            self.barrier.public_barrier.set_to_allowed_on.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline_1 = expected_deadline_1.strftime("%d %B %Y")

        expected_deadline_2 = dateutil.parser.parse(
            self.barrier_2.public_barrier.set_to_allowed_on.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline_2 = expected_deadline_2.strftime("%d %B %Y")

        # Update user to have the approver permission
        self.test_user.groups.add(Group.objects.get(name="Public barrier approver"))
        self.test_user.save()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 2

        # Count the expected task types
        missing_info_task_count = 0
        approve_task_count = 0
        for barrier in response.data["results"]:
            assert barrier["task_list"][0]["tag"] == "OVERDUE REVIEW"
            # Message will be different for barrier with both title and sumary, but we
            # also expect for one of the tasks to be the previously tested message
            if "Approve this barrier" in barrier["task_list"][0]["message"]:
                approve_task_count = approve_task_count + 1
                # Check countdown has been substituted into message
                assert (
                    f"for publication and complete clearance checks by {expected_deadline_1}."
                    in barrier["task_list"][0]["message"]
                )
            elif "Add a public title and summary" in barrier["task_list"][0]["message"]:
                missing_info_task_count = missing_info_task_count + 1
                # Check countdown has been substituted into message
                assert (
                    f"This needs to be done by {expected_deadline_2}."
                    in barrier["task_list"][0]["message"]
                )

        assert approve_task_count == 1
        assert missing_info_task_count == 1

    def test_publishing_task_publisher_user_approve_request(self):
        """This task is for users with publisher permissions only. We need
        to check that the task is added when the barrier is in a specific status"""

        self.public_barrier_setUp()

        # Set barrier to PUBLISHING_PENDING status and give it both title and summary
        self.barrier.public_barrier.public_view_status = (
            PublicBarrierStatus.PUBLISHING_PENDING
        )
        self.barrier.public_barrier.summary = "adding a summary"
        self.barrier.public_barrier.set_to_allowed_date = datetime.now()
        self.barrier.public_barrier.save()

        expected_deadline = dateutil.parser.parse(
            self.barrier.public_barrier.set_to_allowed_date.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline = expected_deadline.strftime("%d %B %Y")

        # Update user to have the publisher permission
        self.test_user.groups.add(Group.objects.get(name="Publisher"))
        self.test_user.save()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 2

        # Count the expected task types
        missing_info_task_count = 0
        publish_task_count = 0
        for barrier in response.data["results"]:
            assert barrier["task_list"][0]["tag"] == "PUBLICATION REVIEW"
            # Message will be different for barrier with both title and sumary, but we
            # also expect for one of the tasks to be the previously tested message
            if "Complete GOV.UK content checks" in barrier["task_list"][0]["message"]:
                publish_task_count = publish_task_count + 1
                # Check countdown has been substituted into message
                assert f"by {expected_deadline}." in barrier["task_list"][0]["message"]
            elif "Add a public title and summary" in barrier["task_list"][0]["message"]:
                missing_info_task_count = missing_info_task_count + 1
                # Check countdown has been substituted into message
                assert (
                    f"This needs to be done by {expected_deadline}."
                    in barrier["task_list"][0]["message"]
                )

        assert publish_task_count == 1
        assert missing_info_task_count == 1

    def test_publishing_task_publisher_user_approve_request_no_permission(self):
        """This task is for users with publisher permissions only. We need
        to check that the task is added when the barrier is in a specific status"""

        self.public_barrier_setUp()

        # Set barrier to PUBLISHING_PENDING status and give it both title and summary
        self.barrier.public_barrier.public_view_status = (
            PublicBarrierStatus.PUBLISHING_PENDING
        )
        self.barrier.public_barrier.summary = "adding a summary"
        self.barrier.public_barrier.set_to_allowed_date = datetime.now()
        self.barrier.public_barrier.save()

        expected_deadline = dateutil.parser.parse(
            self.barrier.public_barrier.set_to_allowed_date.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline = expected_deadline.strftime("%d %B %Y")

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 1

        for barrier in response.data["results"]:
            assert len(barrier["task_list"]) == 1
            assert barrier["task_list"][0]["tag"] == "PUBLICATION REVIEW"
            assert (
                "Add a public title and summary" in barrier["task_list"][0]["message"]
            )
            # Check countdown has been substituted into message
            assert (
                f"This needs to be done by {expected_deadline}."
                in barrier["task_list"][0]["message"]
            )

    def test_publishing_task_publisher_user_approve_request_overdue(self):
        """This task is for users with approver permissions only. We need
        to check that the task is added when the barrier is in a specific status"""

        self.public_barrier_setUp()

        # Set barrier to PUBLISHING_PENDING status and give it both title and summary
        self.barrier.public_barrier.public_view_status = (
            PublicBarrierStatus.PUBLISHING_PENDING
        )
        self.barrier.public_barrier.summary = "adding a summary"
        self.barrier.public_barrier.save()

        # Modify the public barrier missing the title to be overdue by
        # making set_to_allowed_on more than 30 days in the past
        self.barrier.public_barrier.set_to_allowed_on = datetime.now() - timedelta(
            days=40
        )
        self.barrier.public_barrier.save()

        # Modify the public barrier missing the summary to be overdue by
        # making set_to_allowed_on more than 30 days in the past
        self.barrier_2.public_barrier.set_to_allowed_on = datetime.now() - timedelta(
            days=40
        )
        self.barrier_2.public_barrier.save()

        expected_deadline_1 = dateutil.parser.parse(
            self.barrier.public_barrier.set_to_allowed_on.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline_1 = expected_deadline_1.strftime("%d %B %Y")

        expected_deadline_2 = dateutil.parser.parse(
            self.barrier_2.public_barrier.set_to_allowed_on.strftime("%d %B %Y")
        ) + timedelta(days=30)
        expected_deadline_2 = expected_deadline_2.strftime("%d %B %Y")

        # Update user to have the publisher permission
        self.test_user.groups.add(Group.objects.get(name="Publisher"))
        self.test_user.save()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 2

        # Count the expected task types
        missing_info_task_count = 0
        publish_task_count = 0
        for barrier in response.data["results"]:
            assert barrier["task_list"][0]["tag"] == "OVERDUE REVIEW"
            # Message will be different for barrier with both title and sumary, but we
            # also expect for one of the tasks to be the previously tested message
            if "Complete GOV.UK content checks" in barrier["task_list"][0]["message"]:
                publish_task_count = publish_task_count + 1
                # Check countdown has been substituted into message
                assert (
                    f"by {expected_deadline_1}." in barrier["task_list"][0]["message"]
                )
            elif "Add a public title and summary" in barrier["task_list"][0]["message"]:
                missing_info_task_count = missing_info_task_count + 1
                # Check countdown has been substituted into message
                assert (
                    f"This needs to be done by {expected_deadline_2}."
                    in barrier["task_list"][0]["message"]
                )

        assert publish_task_count == 1
        assert missing_info_task_count == 1

    def test_missing_barrier_detail_government_orgs(self):
        """All owned barriers will generate a task if they do not have
        any data stored under 'organisations' attribute"""

        self.basic_barrier_setUp(erd_time="future")
        self.barrier.organisations.clear()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "ADD INFORMATION"
                and "Check and add any other government departments (OGDs)"
                in task["message"]
            ):
                task_found = True
        assert task_found

    def test_missing_barrier_detail_hs_code(self):
        """Barriers that are set as dealing with goods exports
        will generate a task if they do not have a product hs_code set"""

        self.basic_barrier_setUp(erd_time="future")
        self.barrier.export_types.add(ExportType.objects.get(name="goods"))

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "ADD INFORMATION"
                and "Add an HS code to this barrier." in task["message"]
            ):
                task_found = True
        assert task_found

    @freezegun.freeze_time(datetime(2024, 1, 10).replace(tzinfo=timezone.utc))
    def test_missing_barrier_detail_financial_year_delivery_confidence(self):
        """A task will be generated for barriers with an estimated resolution date
        within the current financial year without any progress updates."""

        self.barrier = BarrierFactory(
            estimated_resolution_date=datetime(2024, 1, 20).replace(
                tzinfo=timezone.utc
            ),
        )
        self.barrier.organisations.add(*self.test_government_departments)

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 1
        for barrier in response.data["results"]:
            assert len(barrier["task_list"]) == 1
            assert barrier["task_list"][0]["tag"] == "ADD INFORMATION"
            assert "Add your delivery confidence" in barrier["task_list"][0]["message"]

    def test_missing_barrier_detail_no_tasks_if_resolved(self):
        """Test to ensure tasks dealing with missing details will
        not be added to the task list if the barrier in question is resolved."""
        self.basic_barrier_setUp(erd_time="future")
        self.barrier.export_types.add(ExportType.objects.get(name="goods"))
        self.barrier.status = BarrierStatus.RESOLVED_IN_FULL
        self.barrier.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_erd_tasks_outdated_value(self):
        """A task will be added if the estimated resolution date for the barrier has passed"""

        self.basic_barrier_setUp(erd_time="past")

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 1
        for barrier in response.data["results"]:
            assert len(barrier["task_list"]) == 1
            assert barrier["task_list"][0]["tag"] == "CHANGE OVERDUE"
            assert (
                "Review the estimated resolution date"
                in barrier["task_list"][0]["message"]
            )

    def test_erd_tasks_resolved_wont_trigger_task(self):
        """Ensure that tasks relating to estimated resolution date are not
        added when the related barrier is resolved"""

        self.basic_barrier_setUp(erd_time="past")
        self.barrier.status = BarrierStatus.RESOLVED_IN_FULL
        self.barrier.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 0

    @freezegun.freeze_time(datetime(2024, 1, 10).replace(tzinfo=timezone.utc))
    def test_erd_tasks_missing_for_pb100(self):
        """A task should be created for barriers that are top priority (pb100)
        that have not had an estimated resolution date set"""

        self.basic_barrier_setUp()
        self.barrier.top_priority_status = "APPROVED"
        self.barrier.save()

        # Add progress update to prevent triggering other tasks
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            update="Nothing Specific",
            next_steps="First steps",
            modified_on=datetime.now(),
        )
        progress_update.next_steps = "Edited Steps"
        progress_update.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 1
        for barrier in response.data["results"]:
            assert len(barrier["task_list"]) == 1
            assert barrier["task_list"][0]["tag"] == "ADD DATE"
            assert (
                "Add an estimated resolution date" in barrier["task_list"][0]["message"]
            )

    def test_erd_tasks_missing_for_overseas_delivery(self):
        """A task should be created for barriers that are overseas delivery priority
        that have not had an estimated resolution date set"""

        self.basic_barrier_setUp()
        self.barrier.priority_level = "OVERSEAS"
        self.barrier.save()

        # Add progress update to prevent triggering other tasks
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            update="Nothing Specific",
            next_steps="First steps",
            modified_on=datetime.now(),
        )
        progress_update.next_steps = "Edited Steps"
        progress_update.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 1
        for barrier in response.data["results"]:
            assert len(barrier["task_list"]) == 1
            assert barrier["task_list"][0]["tag"] == "ADD DATE"
            assert (
                "Add an estimated resolution date" in barrier["task_list"][0]["message"]
            )

    def test_erd_tasks_missing_for_overseas_delivery_no_permission(self):
        """Only owners should see these estimated resolution date tasks"""

        self.basic_barrier_setUp()
        self.barrier.priority_level = "OVERSEAS"
        self.barrier.save()

        # Add progress update to prevent triggering other tasks
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            update="Nothing Specific",
            next_steps="First steps",
            modified_on=datetime.now(),
        )
        progress_update.next_steps = "Edited Steps"
        progress_update.save()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 0

    def test_erd_tasks_progress_update_erd_outdated(self):
        """Progress updates contain their own estimated resolution date
        value seperate from the one on the barrier, we expect to add
        a task if this value is outdated."""

        self.basic_barrier_setUp()
        self.barrier.top_priority_status = "APPROVED"
        self.barrier.save()

        # Add progress update with outdated estimated resolution date
        expiry_date = datetime.now() - timedelta(days=181)
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            update="Nothing Specific",
            next_steps="First steps",
            modified_on=datetime(expiry_date.year, expiry_date.month, expiry_date.day),
        )
        progress_update.next_steps = "Edited Steps"
        progress_update.save()

        readable_modified_date = progress_update.modified_on.strftime("%d %B %Y")

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            logger.critical(task["message"])

            if (
                task["tag"] == "REVIEW DATE"
                and "Check the estimated resolution date" in task["message"]
                and f"as it has not been reviewed since {readable_modified_date}."
                in task["message"]
            ):
                task_found = True
        assert task_found

    def test_progress_update_tasks_pb100_mising_progress_update(self):
        """It is intended that top priority (pb100) barriers be tracked with progress updates
        so we expect a task to be added which checks that the barrier is not missing
        a progress update."""

        self.basic_barrier_setUp(erd_time="future")
        self.barrier.top_priority_status = "APPROVED"
        self.barrier.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "PROGRESS UPDATE DUE"
                and "Add a monthly progress update" in task["message"]
            ):
                task_found = True
        assert task_found

    def test_progress_update_tasks_none_when_resolved(self):
        """Test to ensure no progress-update related tasks are added for resolved barriers"""

        self.basic_barrier_setUp(erd_time="future")
        self.barrier.top_priority_status = "APPROVED"
        self.barrier.status = BarrierStatus.RESOLVED_IN_FULL
        self.barrier.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"]:
            if (
                task["tag"] == "PROGRESS UPDATE DUE"
                and "This is a PB100 barrier. Add a monthly progress update"
                in task["message"]
            ):
                task_found = True
        assert not task_found

    @freezegun.freeze_time(datetime(2024, 1, 10).replace(tzinfo=timezone.utc))
    def test_progress_update_tasks_monthly_pb100_update_due(self):
        """It is current practice that there are progress updates for top priority (pb100) barriers
        which are due before the 3rd friday of every month. A task is expected to trigger
        when a pb100 barriers last progress update is between the first of the month and
        the date of the third firday to prompt users to make an update."""

        self.basic_barrier_setUp(erd_time="future")
        self.barrier.top_priority_status = "APPROVED"
        self.barrier.save()

        # Add progress update
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            update="Nothing Specific",
            next_steps="First steps",
            modified_on=datetime(2023, 12, 31),
        )
        progress_update.next_steps = "Edited Steps"
        progress_update.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "PROGRESS UPDATE DUE"
                and "Add a monthly progress update" in task["message"]
                and "to this PB100 barrier by 19 January 2024." in task["message"]
            ):
                task_found = True
        assert task_found

    @freezegun.freeze_time(datetime(2024, 1, 21).replace(tzinfo=timezone.utc))
    def test_progress_update_tasks_monthly_pb100_update_overdue(self):
        """It is current practice that there are progress updates for top priority (pb100) barriers
        which are due before the 3rd friday of every month. A task indicating the update
        is overdue is expected to trigger when a pb100 barriers last progress update is
        after the third friday of the month."""

        self.basic_barrier_setUp(erd_time="future")
        self.barrier.top_priority_status = "APPROVED"
        self.barrier.save()

        # Add progress update
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            update="Nothing Specific",
            next_steps="First steps",
            modified_on=datetime(2023, 12, 31),
        )
        progress_update.next_steps = "Edited Steps"
        progress_update.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "OVERDUE PROGRESS UPDATE"
                and "Add a monthly progress update" in task["message"]
                and "to this PB100 barrier by 19 January 2024." in task["message"]
            ):
                task_found = True
        assert task_found

    def test_progress_update_tasks_overdue_next_steps(self):
        """A task is generated when a next_step item of a progress update
        has a completion_date value in the past."""

        self.basic_barrier_setUp(erd_time="future")
        self.barrier.top_priority_status = "APPROVED"
        self.barrier.save()

        # Create next step item
        BarrierNextStepItem.objects.create(
            barrier=self.barrier,
            status=NEXT_STEPS_ITEMS_STATUS_CHOICES.IN_PROGRESS,
            next_step_owner="Test Owner",
            next_step_item="Test next step item",
            completion_date=datetime.now() - timedelta(days=50),
        )

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        # pytest tests/dashboard/test_views.py::TestDashboardTasksView::test_progress_update_tasks_overdue_next_steps
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            logger.critical(task["message"])
            if (
                task["tag"] == "REVIEW NEXT STEP"
                and "Review the barrier next steps" in task["message"]
            ):
                task_found = True
        assert task_found

    def test_progress_update_due_for_overseas_barriers(self):
        """A task is generated when a barrier with overseas delivery priority level
        had its latest progress update over 90 days ago."""

        self.basic_barrier_setUp(erd_time="future")
        self.barrier.priority_level = "OVERSEAS"
        self.barrier.save()

        # Add progress update
        progress_update = BarrierProgressUpdate.objects.create(
            barrier=self.barrier,
            status=PROGRESS_UPDATE_CHOICES.ON_TRACK,
            update="Nothing Specific",
            next_steps="First steps",
            modified_on=datetime(2023, 12, 31),
        )
        progress_update.next_steps = "Edited Steps"
        progress_update.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "PROGRESS UPDATE DUE"
                and "Add a quarterly progress update" in task["message"]
                and "to this overseas delivery barrier." in task["message"]
            ):
                task_found = True
        assert task_found

    def test_progress_update_missing_for_overseas_barriers(self):
        """A task is generated when a barrier with overseas delivery priority level
        has not had a progress update."""

        self.basic_barrier_setUp(erd_time="future")
        self.barrier.priority_level = "OVERSEAS"
        self.barrier.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "PROGRESS UPDATE DUE"
                and "Add a quarterly progress update" in task["message"]
                and "to this overseas delivery barrier." in task["message"]
            ):
                task_found = True
        assert task_found

    def test_progress_update_overdue_for_programme_fund_barriers(self):
        """Barriers which are tagged with a Programme Fund tag need
        programme fund progress updates, if the latest update is more
        than 90 days old we create a task."""

        self.basic_barrier_setUp(erd_time="future")

        # Add programme fund progress update
        pf = ProgrammeFundProgressUpdateFactory(barrier=self.barrier)
        pf.modified_on = datetime.now() - timedelta(days=200)
        pf.save()

        # Add programme fund tag to barrier
        programme_fund_tag = BarrierTag.objects.get(
            title="Programme Fund - Facilitative Regional"
        )
        self.barrier.tags.add(programme_fund_tag)

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "PROGRESS UPDATE DUE"
                and "Add a programme fund update" in task["message"]
                and "to this barrier." in task["message"]
            ):
                task_found = True
        assert task_found

    def test_progress_update_missing_for_programme_fund_barriers(self):
        """Barriers with the Programme Fund - Faciliative Regional tag
        assigned should hace a programme fund progress update, a task is added
        if it is missing."""

        self.basic_barrier_setUp(erd_time="future")

        # Add programme fund tag to barrier
        programme_fund_tag = BarrierTag.objects.get(
            title="Programme Fund - Facilitative Regional"
        )
        self.barrier.tags.add(programme_fund_tag)

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "PROGRESS UPDATE DUE"
                and "Add a programme fund update" in task["message"]
                and "to this barrier." in task["message"]
            ):
                task_found = True
        assert task_found

    def test_mentions_task_list(self):
        """Mentions are when another user uses an @ followed by another users
        email in a barrier note to flag to that user that they need to pay attention.
        Mentions with a user indicated should create a task that is added to the task list.
        """

        self.basic_barrier_setUp(erd_time="future")

        text = f"test mention @{self.user.email}"
        interaction = Interaction(
            created_by=self.test_user,
            barrier=self.barrier,
            kind="kind",
            text=text,
            pinned=False,
            is_active=True,
        )
        interaction.save()

        mention = Mention(
            barrier=self.barrier,
            email_used=self.test_user_2.email,
            recipient=self.test_user,
            created_by_id=self.test_user_2.id,
        )
        mention.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "REVIEW COMMENT"
                and f"{self.test_user_2.first_name} {self.test_user_2.last_name} mentioned you in on"
                in task["message"]
                and f"{mention.created_on.strftime('%d %B %Y')}." in task["message"]
            ):
                task_found = True
        assert task_found

    def test_mentions_task_list_append_to_existing_list(self):
        """Mentions are when another user uses an @ followed by another users
        email in a barrier note to flag to that user that they need to pay attention.
        Mentions with a user indicated should create a task that is added to the task list.
        """

        self.basic_barrier_setUp(erd_time="future")
        # Ensure another task will be triggered by the barrier
        self.barrier.export_types.add(ExportType.objects.get(name="goods"))

        text = f"test mention @{self.user.email}"
        interaction = Interaction(
            created_by=self.test_user,
            barrier=self.barrier,
            kind="kind",
            text=text,
            pinned=False,
            is_active=True,
        )
        interaction.save()

        mention = Mention(
            barrier=self.barrier,
            email_used=self.test_user_2.email,
            recipient=self.test_user,
            created_by_id=self.test_user_2.id,
        )
        mention.save()

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "REVIEW COMMENT"
                and f"{self.test_user_2.first_name} {self.test_user_2.last_name} mentioned you in on"
                in task["message"]
                and f"{mention.created_on.strftime('%d %B %Y')}." in task["message"]
            ):
                task_found = True
        assert task_found

    def test_mentions_task_list_no_barriers(self):
        """Mentions show up in the task list and are unrelated to
        barriers owned/related to the user, so we would expect mention tasks
        to appear in the task_list if the user is mentioned in a note for
        a barrier they have not previously worked on."""

        self.basic_barrier_setUp(erd_time="future")

        text = f"test mention @{self.user.email}"
        interaction = Interaction(
            created_by=self.test_user,
            barrier=self.barrier,
            kind="kind",
            text=text,
            pinned=False,
            is_active=True,
        )
        interaction.save()

        mention = Mention(
            barrier=self.barrier,
            email_used=self.test_user_2.email,
            recipient=self.test_user,
            created_by_id=self.test_user_2.id,
        )
        mention.save()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        task_found = False
        response.data["results"][0]["barrier_id"] = self.barrier.id
        for task in response.data["results"][0]["task_list"]:
            if (
                task["tag"] == "REVIEW COMMENT"
                and f"{self.test_user_2.first_name} {self.test_user_2.last_name} mentioned you in on"
                in task["message"]
                and f"{mention.created_on.strftime('%d %B %Y')}." in task["message"]
            ):
                task_found = True
        assert task_found

    def test_task_list_pagination(self):
        """The results are paginated so the frontend does not get swamped with tasks
        and overwhelm the user. We expect a maximum of 3 tasks that get returned
        at a time, and that if we are on a second or third page, we get the next
        block of tasks in the list."""

        # Create barriers that will trigger more than 5 entries
        self.barrier = BarrierFactory()
        self.barrier.top_priority_status = "APPROVED"
        self.barrier.save()

        barrier_build_count = 0
        while barrier_build_count < 7:
            additional_barrier = BarrierFactory()
            additional_barrier.priority_level = "OVERSEAS"
            additional_barrier.save()

            # Test requires user to be added to additional barrier
            team_member = TeamMember.objects.create(
                barrier=additional_barrier,
                user=self.test_user,
                created_by=self.test_user,
                role="Owner",
            )
            additional_barrier.barrier_team.add(team_member)
            barrier_build_count += 1

        self.owner_user_setUp()

        response = self.api_client.get(self.request_url)

        assert response.status_code == 200
        assert response.data["count"] == 8
        assert len(response.data["results"]) == 3

        self.request_url_page_2 = f'{reverse("get-dashboard-tasks")}?page=2'
        response_page_2 = self.api_client.get(self.request_url_page_2)

        assert response_page_2.status_code == 200
        assert response_page_2.data["count"] == 8
        assert len(response_page_2.data["results"]) == 3
