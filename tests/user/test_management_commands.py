from typing import Dict, List
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.db import models
from django.db.transaction import atomic
from django.test import TestCase
import uuid

from api.assessment.models import (
    EconomicAssessment,
    EconomicImpactAssessment,
    ResolvabilityAssessment,
    StrategicAssessment,
)
from api.barriers.models import (
    Barrier,
    BarrierReportStage,
    BarrierUserHit,
    PublicBarrier,
    Stage,
)
from api.core.test_utils import create_test_user
from api.documents.models import Document
from api.interactions.models import (
    ExcludeFromNotification,
    Interaction,
    Mention,
    PublicBarrierNote,
    TeamMember,
)
from api.metadata.models import BarrierTag
from api.user.models import (
    MyBarriersSavedSearch,
    SavedSearch,
    TeamBarriersSavedSearch,
)
from api.user_event_log.models import UserEvent

base_models: List[models.Model] = [
    Barrier,
    BarrierReportStage,
    BarrierTag,
    Document,
    EconomicAssessment,
    EconomicImpactAssessment,
    ExcludeFromNotification,
    Interaction,
    Mention,
    PublicBarrier,
    PublicBarrierNote,
    ResolvabilityAssessment,
    StrategicAssessment,
    TeamMember,
]
user_models: List[models.Model] = [
    BarrierUserHit,
    MyBarriersSavedSearch,
    SavedSearch,
    TeamBarriersSavedSearch,
    TeamMember,
    UserEvent,
]
archive_by_models: List[models.Model] = [
    Barrier,
    Document,
    EconomicAssessment,
    EconomicImpactAssessment,
    Interaction,
    PublicBarrier,
    PublicBarrierNote,
    StrategicAssessment,
    TeamMember,
]
unarchived_by_models: List[models.Model] = [Barrier, PublicBarrier]
reviewed_by_models: List[models.Model] = [
    StrategicAssessment,
    ResolvabilityAssessment,
]
excluded_user_models: List[models.Model] = [ExcludeFromNotification]
recipient_models: List[models.Model] = [Mention]


class TestBadUsersBugFix(TestCase):
    def setUp(self):
        super().setUp()
        self.bad_user = create_test_user()
        self.good_user = create_test_user()

        self.notification_patch = patch(
            "api.interactions.models.NotificationsAPIClient"
        )
        self.notification_mock = self.notification_patch.start()

    def tearDown(self):
        self.notification_patch.stop()

    @atomic
    def create_data_records(self, test_user: models.Model) -> Dict[str, models.Model]:
        rand_str: str = str(uuid.uuid4())[:20]
        data_row: Dict[str, models.Model] = {}

        data_row["Barrier"] = Barrier.objects.create(
            created_by=test_user,
            modified_by=test_user,
            archived_by=test_user,
            unarchived_by=test_user,
        )
        stage = Stage.objects.create(
            code="test", description="this is a test"
        )  # Need for fixture
        data_row["BarrierReportStage"] = BarrierReportStage.objects.create(
            created_by=test_user,
            modified_by=test_user,
            barrier=data_row["Barrier"],
            stage=stage,
        )
        data_row["BarrierTag"] = BarrierTag.objects.create(
            created_by=test_user, modified_by=test_user, title=rand_str
        )
        data_row["Document"] = Document.objects.create(
            created_by=test_user,
            modified_by=test_user,
            archived_by=test_user,
            path=rand_str,
        )
        data_row["EconomicAssessment"] = EconomicAssessment.objects.create(
            created_by=test_user,
            modified_by=test_user,
            archived_by=test_user,
            reviewed_by=test_user,
            barrier=data_row["Barrier"],
        )
        data_row["EconomicImpactAssessment"] = EconomicImpactAssessment.objects.create(
            created_by=test_user,
            modified_by=test_user,
            archived_by=test_user,
            economic_assessment=data_row["EconomicAssessment"],
            impact=4,
        )
        data_row["ExcludeFromNotification"] = ExcludeFromNotification.objects.create(
            created_by=test_user,
            modified_by=test_user,
            excluded_user=test_user,
        )
        data_row["Interaction"] = Interaction.objects.create(
            created_by=test_user,
            modified_by=test_user,
            barrier=data_row["Barrier"],
            archived_by=test_user,
        )
        data_row["Mention"] = Mention.objects.create(
            created_by=test_user,
            modified_by=test_user,
            recipient=test_user,
            barrier=data_row["Barrier"],
        )
        data_row["PublicBarrier"] = PublicBarrier.objects.get(
            barrier=data_row["Barrier"]
        )
        data_row["PublicBarrier"].created_by = test_user
        data_row["PublicBarrier"].modified_by = test_user
        data_row["PublicBarrier"].archived_by = test_user
        data_row["PublicBarrier"].unarchived_by = test_user
        data_row["PublicBarrier"].save()
        data_row["PublicBarrierNote"] = PublicBarrierNote.objects.create(
            created_by=test_user,
            modified_by=test_user,
            archived_by=test_user,
            public_barrier=data_row["PublicBarrier"],
        )
        data_row["ResolvabilityAssessment"] = ResolvabilityAssessment.objects.create(
            created_by=test_user,
            modified_by=test_user,
            reviewed_by=test_user,
            barrier=data_row["Barrier"],
            time_to_resolve=2,
            effort_to_resolve=2,
        )
        data_row["StrategicAssessment"] = StrategicAssessment.objects.create(
            created_by=test_user,
            modified_by=test_user,
            archived_by=test_user,
            reviewed_by=test_user,
            barrier=data_row["Barrier"],
            scale=2,
        )
        data_row["TeamMember"] = TeamMember.objects.create(
            created_by=test_user,
            modified_by=test_user,
            archived_by=test_user,
            user=test_user,
            barrier=data_row["Barrier"],
        )
        data_row["BarrierUserHit"] = BarrierUserHit.objects.create(
            user=test_user,
            barrier=data_row["Barrier"],
        )
        data_row["MyBarriersSavedSearch"] = MyBarriersSavedSearch.objects.create(
            user=test_user,
        )
        data_row["SavedSearch"] = SavedSearch.objects.create(user=test_user, filters={})
        data_row["TeamBarriersSavedSearch"] = TeamBarriersSavedSearch.objects.create(
            user=test_user,
        )
        data_row["UserEvent"] = UserEvent.objects.create(
            user=test_user,
        )

        return data_row

    def check_count_on_all_objects(
        self, test_user: settings.AUTH_USER_MODEL, expected_count: 0
    ):
        def _check_orm_attribute(klass: settings.AUTH_USER_MODEL, attribute: str):
            name: str = klass.__name__
            res: int = klass.objects.filter(**{attribute: test_user}).count()

            # There can only be one or zero of these objects
            if klass in [
                MyBarriersSavedSearch,
                TeamBarriersSavedSearch,
                ExcludeFromNotification,
            ]:
                expected_val: int = int(bool(expected_count))
                assert (
                    res == expected_val
                ), f"failed on object {name} attribute {attribute} expected {expected_count}"
                return

            assert (
                res == expected_count
            ), f"failed on object {name} attribute {attribute}"

        for klass in base_models:
            _check_orm_attribute(klass, "created_by")
            _check_orm_attribute(klass, "modified_by")

        for klass in user_models:
            _check_orm_attribute(klass, "user")

        for klass in archive_by_models:
            _check_orm_attribute(klass, "archived_by")

        for klass in unarchived_by_models:
            _check_orm_attribute(klass, "unarchived_by")

        for klass in reviewed_by_models:
            _check_orm_attribute(klass, "reviewed_by")

        for klass in excluded_user_models:
            _check_orm_attribute(klass, "excluded_user")

        for klass in recipient_models:
            _check_orm_attribute(klass, "recipient")

    def test_one_bad_user(self):
        data_row = self.create_data_records(self.bad_user)

        self.check_count_on_all_objects(self.good_user, 0)
        self.check_count_on_all_objects(self.bad_user, 1)

        call_command(
            "fix_bad_users_bugfix_mar919",
            bad_user_id=self.bad_user.id,
            good_user_id=self.good_user.id,
        )

        self.check_count_on_all_objects(self.good_user, 1)
        self.check_count_on_all_objects(self.bad_user, 0)

    def test_one_bad_user_impo(self):
        data_row = self.create_data_records(self.bad_user)

        self.check_count_on_all_objects(self.good_user, 0)
        self.check_count_on_all_objects(self.bad_user, 1)

        call_command(
            "fix_bad_users_bugfix_mar919",
            bad_user_id=self.bad_user.id,
            good_user_id=self.good_user.id,
        )

        self.check_count_on_all_objects(self.good_user, 1)
        self.check_count_on_all_objects(self.bad_user, 0)

        call_command(
            "fix_bad_users_bugfix_mar919",
            bad_user_id=self.bad_user.id,
            good_user_id=self.good_user.id,
        )

        self.check_count_on_all_objects(self.good_user, 1)
        self.check_count_on_all_objects(self.bad_user, 0)

    def test_one_bad_user_one_good(self):
        data_row1 = self.create_data_records(self.bad_user)
        data_row2 = self.create_data_records(self.good_user)

        self.check_count_on_all_objects(self.good_user, 1)
        self.check_count_on_all_objects(self.bad_user, 1)

        call_command(
            "fix_bad_users_bugfix_mar919",
            bad_user_id=self.bad_user.id,
            good_user_id=self.good_user.id,
        )


    def test_two_users_one_barrier(self):
        data_row1 = self.create_data_records(self.bad_user)
        data_row2 = self.create_data_records(self.good_user)

        self.check_count_on_all_objects(self.good_user, 1)
        self.check_count_on_all_objects(self.bad_user, 1)

        dupped = BarrierUserHit.objects.create(
            user=self.good_user,
            barrier=data_row1["Barrier"],
        )

        call_command(
            "fix_bad_users_bugfix_mar919",
            bad_user_id=self.bad_user.id,
            good_user_id=self.good_user.id,
        )

        self.check_count_on_all_objects(self.good_user, 2)
        self.check_count_on_all_objects(self.bad_user, 0)

    def test_one_good_user(self):
        data_row = self.create_data_records(self.good_user)

        self.check_count_on_all_objects(self.good_user, 1)
        self.check_count_on_all_objects(self.bad_user, 0)

        call_command(
            "fix_bad_users_bugfix_mar919",
            bad_user_id=self.bad_user.id,
            good_user_id=self.good_user.id,
        )

        self.check_count_on_all_objects(self.good_user, 1)
        self.check_count_on_all_objects(self.bad_user, 0)

    def test_one_random_user(self):
        junk_user1 = create_test_user()

        data_row1 = self.create_data_records(self.bad_user)
        data_row2 = self.create_data_records(self.good_user)
        data_row3 = self.create_data_records(junk_user1)

        self.check_count_on_all_objects(self.good_user, 1)
        self.check_count_on_all_objects(self.bad_user, 1)
        self.check_count_on_all_objects(junk_user1, 1)

        call_command(
            "fix_bad_users_bugfix_mar919",
            bad_user_id=self.bad_user.id,
            good_user_id=self.good_user.id,
        )

        self.check_count_on_all_objects(self.good_user, 2)
        self.check_count_on_all_objects(self.bad_user, 0)
        self.check_count_on_all_objects(junk_user1, 1)
