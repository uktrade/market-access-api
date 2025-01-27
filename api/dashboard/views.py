import logging
from datetime import datetime, time, timedelta

import dateutil.parser
import pytz
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import F
from django.db.models import Q, ExpressionWrapper, DateTimeField, Value, CharField, OuterRef, Exists, \
    Case, When
from django.db.models.functions import Concat, Greatest
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response

from api.barriers.models import Barrier, BarrierFilterSet, BarrierProgressUpdate, BarrierNextStepItem, \
    ProgrammeFundProgressUpdate
from api.barriers.serializers import BarrierListSerializer
from api.collaboration.models import TeamMember
from api.core.date_utils import get_nth_day_of_month
from api.dashboard import service
from api.dashboard.service import get_financial_year_dates
from api.interactions.models import Mention
from api.metadata.constants import TOP_PRIORITY_BARRIER_STATUS, GOVERNMENT_ORGANISATION_TYPES

logger = logging.getLogger(__name__)


class BarrierDashboardSummary(generics.GenericAPIView):
    """
    View to return high level stats to the dashboard
    """

    serializer_class = BarrierListSerializer
    filterset_class = BarrierFilterSet

    filter_backends = (DjangoFilterBackend,)
    ordering_fields = (
        "reported_on",
        "modified_on",
        "estimated_resolution_date",
        "status",
        "priority",
        "country",
    )
    ordering = ("-reported_on",)

    def get(self, request):
        filtered_queryset = self.filter_queryset(
            Barrier.barriers.filter(archived=False)
        )

        counts = service.get_counts(qs=filtered_queryset, user=request.user)

        return Response(counts)


def create_editor_task(barrier):
    overdue = barrier["deadline"].replace(tzinfo=None) < datetime.today() if barrier["deadline"] else ""
    deadline = barrier['deadline'].strftime('%d %B %Y') if barrier["deadline"] else ""
    if barrier["public_barrier_title"] and barrier["public_barrier_summary"]:
        return {
            "tag": "OVERDUE REVIEW" if overdue else "PUBLICATION REVIEW",
            "message": [
                "Submit for clearance checks and GOV.UK publication approval",
                f"by {deadline}." if deadline else "",
            ],
            "task_url": "barriers:public_barrier_detail",
            "link_text": "Submit for clearance checks and GOV.UK publication approval",
        }
    else:
        return {
            "tag": "OVERDUE REVIEW" if overdue else "PUBLICATION REVIEW",
            "message": [
                "Add a public title and summary",
                "to this barrier before it can be approved.",
                f"This needs to be done by {deadline}." if deadline else "",
            ],
            "task_url": "barriers:public_barrier_detail",
            "link_text": "Add a public title and summary",
        }


def create_approver_task(barrier):
    overdue = barrier["deadline"].replace(tzinfo=None) < datetime.today() if barrier["deadline"] else ""
    deadline = barrier['deadline'].strftime('%d %B %Y') if barrier["deadline"] else ""

    return {
        "tag": "OVERDUE REVIEW" if overdue else "PUBLICATION REVIEW",
        "message": [
            "Approve this barrier",
            f"for publication and complete clearance checks by {deadline}." if deadline else "",
            "It can then be submitted to the GOV.UK content team.",
        ],
        "task_url": "barriers:public_barrier_detail",
        "link_text": "Approve this barrier",
    }


def create_publisher_task(barrier):
    overdue = barrier["deadline"].replace(tzinfo=None) < datetime.today() if barrier["deadline"] else ""
    deadline = barrier['deadline'].strftime('%d %B %Y') if barrier["deadline"] else ""

    return {
        "tag": "OVERDUE REVIEW" if overdue else "PUBLICATION REVIEW",
        "message": [
            "Complete GOV.UK content checks",
            f"by {deadline}." if deadline else "",
        ],
        "task_url": "barriers:public_barrier_detail",
        "link_text": "Complete GOV.UK content checks",
    }


def create_barrier_entry(barrier):
    return {
        "barrier_id": str(barrier["id"]),
        "barrier_code": barrier["code"],
        "barrier_title": barrier["title"],
        "modified_by": barrier["full_name"],
        "modified_on": barrier["modified_on"].strftime("%d %B %Y") if barrier["modified_on"] else "Unknown",
        "task_list": [],
    }


def create_progress_update_task(barrier):
    today = datetime.today()
    first_of_month_date = today.replace(day=1, tzinfo=pytz.UTC)
    third_friday_day = get_nth_day_of_month(year=today.year, month=today.month, nth=3, weekday=4)
    third_fridate_date = today.replace(day=third_friday_day)
    if not barrier["progress_update_modified_on"] or (
        barrier["progress_update_modified_on"] < first_of_month_date
        and today < third_fridate_date
    ):
        tag = "PROGRESS UPDATE DUE"
    elif barrier["progress_update_modified_on"] < first_of_month_date and today > third_fridate_date:
        tag = "OVERDUE PROGRESS UPDATE"
    else:
        return

    return {
        "tag": tag,
        "message": [
            "Add a monthly progress update",
            f"to this PB100 barrier by {third_fridate_date.strftime('%d %B %Y')}.",
        ],
        "task_url": "barriers:add_progress_update",
        "link_text": "Add a monthly progress update",
    }


def create_next_step_task(_):
    return {
        "tag": "REVIEW NEXT STEP",
        "message": [
            "Review the barrier next steps",
        ],
        "task_url": "barriers:list_next_steps",
        "link_text": "Review the next steps",
    }


def create_overseas_task(_):
    return {
        "tag": "PROGRESS UPDATE DUE",
        "message": [
            "Add a quarterly progress update",
            "to this overseas delivery barrier.",
        ],
        "task_url": "barriers:add_progress_update",
        "link_text": "Add a quarterly progress update",
    }


def create_programme_fund_update_task(_):
    return {
        "tag": "PROGRESS UPDATE DUE",
        "message": ["Add a programme fund update", "to this barrier."],
        "task_url": "barriers:add_programme_fund_progress_update",
        "link_text": "Add a programme fund update",
    }


def create_missing_hs_code_task(_):
    return {
        "tag": "ADD INFORMATION",
        "message": ["Add an HS code to this barrier."],
        "task_url": "barriers:edit_commodities",
        "link_text": "Add an HS code to this barrier.",
    }


def create_missing_gov_org_task(_):
    return {
        "tag": "ADD INFORMATION",
        "message": [
            "Check and add any other government departments (OGDs)",
            "involved in the resolution of this barrier.",
        ],
        "task_url": "barriers:edit_gov_orgs",
        "link_text": "Check and add any other government departments (OGDs)",
    }


def create_add_progress_update_task(_):
    return {
        "tag": "ADD INFORMATION",
        "message": [
            "Add your delivery confidence",
            "to this barrier.",
        ],
        "task_url": "barriers:add_progress_update",
        "link_text": "Add your delivery confidence",
    }


def create_overdue_erd_task(barrier):
    return {
        "tag": "CHANGE OVERDUE",
        "message": [
            "Review the estimated resolution date",
            f"as it is currently listed as {barrier['estimated_resolution_date']},",
            "which is in the past.",
        ],
        "task_url": "barriers:edit_estimated_resolution_date",
        "link_text": "Review the estimated resolution date",
    }


def create_add_priority_erd_task(_):
    return {
        "tag": "ADD DATE",
        "message": [
            "Add an estimated resolution date",
            "to this PB100 barrier.",
        ],
        "task_url": "barriers:edit_estimated_resolution_date",
        "link_text": "Add an estimated resolution date",
    }


def create_review_priority_erd_task(barrier):
    return {
        "tag": "REVIEW DATE",
        "message": [
            "Check the estimated resolution date",
            f"as it has not been reviewed since {barrier['progress_update_modified_on'].strftime('%d %B %Y')}.",
        ],
        "task_url": "barriers:edit_estimated_resolution_date",
        "link_text": "Check the estimated resolution date",
    }


def create_mentions_task(mention):
    return {
        "tag": "REVIEW COMMENT",
        "message": [
            "Reply to the comment",
            f"{mention['first_name']} {mention['last_name']} mentioned you in on",
            f"{mention['created_on'].strftime('%d %B %Y')}.",
        ],
        "task_url": "barriers:barrier_detail",
        "link_text": "Reply to the comment",
    }


def get_combined_barrier_mention_qs(user):
    return (
        Barrier.objects.filter(
            Q(barrier_team__user=user)
            & Q(barrier_team__archived=False)
            & Q(archived=False)
        )
        .annotate(
            modified_on_union=Case(
                When(
                    Exists(
                        Mention.objects.filter(
                            barrier__id=OuterRef('pk'),
                            recipient=user,
                            created_on__date__gte=(datetime.now() - timedelta(days=30))
                        )
                    ),
                    then=Greatest(
                        Mention.objects.filter(
                            barrier__id=OuterRef('pk'),
                            recipient=user,
                            created_on__date__gte=(datetime.now() - timedelta(days=30))
                        ).order_by("-created_on").values("created_on")[:1],
                        F("modified_on")
                    ),
                ),
                default=F("modified_on"),
                output_field=DateTimeField()

            )
        )
        .order_by("-modified_on_union")
        .distinct()
    )


def get_tasks(user):
    user_groups = set(user.groups.values_list("name", flat=True))
    public_view_statuses = [20]
    fy_start_date, fy_end_date, _, __ = get_financial_year_dates()
    if "Public barrier approver" in user_groups:
        public_view_statuses.append(70)
    if "Publisher" in user_groups:
        public_view_statuses.append(30)
    barrier_entries = []

    qs = get_combined_barrier_mention_qs(user)

    qs = qs.annotate(
        is_owner=Exists(TeamMember.objects.filter(
            barrier=OuterRef("pk"), role=TeamMember.OWNER, user=user, archived=False
        )),
        deadline=ExpressionWrapper(
            F("public_barrier__set_to_allowed_on") + timedelta(days=30), output_field=DateTimeField()
        ),
        full_name=Concat(
            F("modified_by__first_name"), Value(' '), F("modified_by__last_name"),
            output_field=CharField()
        ),
        progress_update_modified_on=BarrierProgressUpdate.objects.filter(
            barrier=OuterRef("pk")
        ).order_by("-created_on").values("modified_on")[:1],
        has_overdue_next_step=Exists(
            BarrierNextStepItem.objects.filter(
                barrier=OuterRef("pk"),
                status="IN_PROGRESS",
                completion_date__lt=datetime.date(datetime.today())
            )
        ),
        latest_programme_fund_modified_on=ProgrammeFundProgressUpdate.objects.filter(
            barrier=OuterRef("pk")
        ).order_by("-created_on").values("modified_on")[:1],
        has_programme_fund_tag=Exists(
            Barrier.objects.filter(pk=OuterRef("pk"), tags__title="Programme Fund - Facilitative Regional")
        ),
        has_goods=Exists(
            Barrier.objects.filter(
                id=OuterRef("pk"),
                export_types__name="goods"
            )
        ),
        has_commodities=Exists(
            Barrier.objects.filter(
                id=OuterRef("pk"),
                commodities__commodity__isnull=False
            )
        ),
        has_government_organisation=Exists(
            Barrier.objects.filter(
                id=OuterRef("pk"),
                organisations__organisation_type__in=GOVERNMENT_ORGANISATION_TYPES
            )
        )
    ).values(
        "id",
        "modified_on_union",
        "title",
        "code",
        "deadline",
        "is_owner",
        "modified_on",
        "full_name",
        "status",
        "top_priority_status",
        "progress_update_modified_on",
        "has_overdue_next_step",
        "priority_level",
        "has_programme_fund_tag",
        "latest_programme_fund_modified_on",
        "has_goods",
        "has_commodities",
        "has_government_organisation",
        "estimated_resolution_date",
        set_to_allowed_on=F("public_barrier__set_to_allowed_on"),
        public_barrier_title=F("public_barrier___title"),
        public_barrier_summary=F("public_barrier___summary"),
        public_view_status=F("public_barrier___public_view_status")
    )
    mentions = Mention.objects.filter(
        barrier__id__in=[b["id"] for b in qs],
        recipient=user,
        created_on__date__gte=(datetime.now() - timedelta(days=30))
    ).values("created_on", "barrier", first_name=F("created_by__first_name"), last_name=F("created_by__last_name"))
    mentions_lookup = {m["barrier"]: m for m in mentions}

    for barrier in qs:
        barrier_entry = create_barrier_entry(barrier)
        if barrier["is_owner"] and barrier["public_view_status"] == 20:
            task = create_editor_task(barrier)
            barrier_entry["task_list"].append(task)

        if "Public barrier approver" in user_groups and barrier["public_view_status"] == 70:
            task = create_approver_task(barrier)
            barrier_entry["task_list"].append(task)

        if "Publisher" in user_groups and barrier["public_view_status"] == 30:
            task = create_publisher_task(barrier)
            barrier_entry["task_list"].append(task)

        if barrier["status"] in {1, 2, 3} and barrier["top_priority_status"] in {
            TOP_PRIORITY_BARRIER_STATUS.APPROVED,
            TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING,
        }:
            task = create_progress_update_task(barrier)
            if task:
                barrier_entry["task_list"].append(task)

            if barrier["has_overdue_next_step"]:
                task = create_next_step_task(barrier)
                barrier_entry["task_list"].append(task)

        if (
            barrier["status"] in {1, 2, 3} and
            barrier["priority_level"] == "OVERSEAS" and
            (
                not barrier["progress_update_modified_on"] or
                barrier["progress_update_modified_on"] < datetime.today() - timedelta(days=90)
            )
        ):
            task = create_overseas_task(barrier)
            barrier_entry["task_list"].append(task)

        if barrier["has_programme_fund_tag"] and (
            not barrier["latest_programme_fund_modified_on"] or
            barrier["latest_programme_fund_modified_on"] < (datetime.today() - timedelta(days=90)).replace(tzinfo=pytz.UTC)
        ):
            task = create_programme_fund_update_task(barrier)
            barrier_entry["task_list"].append(task)

        # Barrier missing details
        if (
            barrier["status"] in {1, 2, 3} and
            barrier["has_goods"] and
            not barrier["has_commodities"]
        ):
            task = create_missing_hs_code_task(barrier)
            barrier_entry["task_list"].append(task)

        if barrier["status"] in {1, 2, 3} and not barrier["has_government_organisation"]:
            task = create_missing_gov_org_task(barrier)
            barrier_entry["task_list"].append(task)

        if (
            barrier["status"] in {1, 2, 3} and
            barrier["estimated_resolution_date"] and
            not barrier["progress_update_modified_on"] and
            barrier["estimated_resolution_date"] < fy_end_date and
            barrier["estimated_resolution_date"] > fy_start_date
        ):
            task = create_add_progress_update_task(barrier)
            barrier_entry["task_list"].append(task)

        if (
                barrier["status"] in {1, 2, 3} and
                barrier["estimated_resolution_date"] and
                barrier["estimated_resolution_date"] < datetime.today().date()
        ):
            task = create_overdue_erd_task(barrier)
            barrier_entry["task_list"].append(task)

        if (
                barrier["is_owner"] and
                (
                    barrier["top_priority_status"] in {
                        TOP_PRIORITY_BARRIER_STATUS.APPROVED,
                        TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING,
                    } or barrier['priority_level'] == "OVERSEAS"
                ) and
                not barrier["estimated_resolution_date"]
        ):
            task = create_add_priority_erd_task(barrier)
            barrier_entry["task_list"].append(task)

        if (
                barrier["is_owner"] and
                barrier["top_priority_status"] in {
                    TOP_PRIORITY_BARRIER_STATUS.APPROVED,
                    TOP_PRIORITY_BARRIER_STATUS.REMOVAL_PENDING,
                } and
                barrier["progress_update_modified_on"] and
                barrier["progress_update_modified_on"] < (datetime.now() - timedelta(days=180)).replace(tzinfo=pytz.UTC)
        ):
            task = create_review_priority_erd_task(barrier)
            barrier_entry["task_list"].append(task)

        if barrier["id"] in mentions_lookup:
            mention = mentions_lookup[barrier["id"]]
            task = create_mentions_task(mention)
            barrier_entry["task_list"].append(task)

        if barrier_entry["task_list"]:
            barrier_entries.append(barrier_entry)

    return barrier_entries


class UserTasksView(generics.ListAPIView):
    """
    Returns list of dashboard next steps, tasks and progress updates
    related to barriers where a given user is either owner or
    collaborator.
    """

    # Set variables used in date related calculations
    todays_date = datetime.now(timezone.utc)
    publishing_overdue = False
    publish_deadline = ""
    third_friday_date = None
    first_of_month_date = None

    def get(self, request, *args, **kwargs):
        # Get the User information from the request
        user = request.user
        user_groups = user.groups.all()

        # Can use filter from search without excluding barriers that the user owns to
        # get the full list of barriers they should be getting task list for
        users_barriers = (
            Barrier.objects.filter(
                Q(barrier_team__user=user)
                & Q(barrier_team__archived=False)
                & Q(archived=False)
            )
            .distinct()
            .order_by("-modified_on")
            .select_related("public_barrier")
            .prefetch_related(
                "progress_updates",
                "barrier_team",
                "barrier_commodities",
                "next_steps_items",
                "tags",
                "export_types",
                "modified_by",
            )
        )

        # Initialise task list
        task_list = []

        # With the list of barriers the user could potentially see, we now need to build a list of
        # tasks derived from conditions the barriers in the list are in.
        for barrier in users_barriers:
            barrier_entry = self.create_barrier_entry(barrier)

            # Check if the barrier is overdue for publishing
            self.check_publishing_overdue(barrier)

            # Establish the relationship between the user and barrier
            is_owner, is_approver, is_publisher = self.get_user_barrier_relations(
                user, user_groups, barrier
            )

            # Only barrier owners should get notifications for public barrier editing
            if is_owner:
                publishing_editor_task = self.check_public_barrier_editor_tasks(barrier)

                if publishing_editor_task:
                    barrier_entry["task_list"].append(publishing_editor_task)

            # Only add public barrier approver tasks for users with that role
            if is_approver:
                publishing_approver_task = self.check_public_barrier_approver_tasks(
                    barrier
                )
                barrier_entry["task_list"].append(publishing_approver_task)

            # Only add public barrier publisher tasks for users with that role
            if is_publisher:
                publishing_publisher_task = self.check_public_barrier_publisher_tasks(
                    barrier
                )
                barrier_entry["task_list"].append(publishing_publisher_task)

            if barrier.status in [1, 2, 3]:
                progress_update_tasks = self.check_progress_update_tasks(barrier)
                barrier_entry["task_list"] += progress_update_tasks

            missing_barrier_tasks = self.check_missing_barrier_details(barrier)
            barrier_entry["task_list"] += missing_barrier_tasks

            estimated_resolution_date_tasks = (
                self.check_estimated_resolution_date_tasks(user, barrier)
            )
            barrier_entry["task_list"] += estimated_resolution_date_tasks

            # Remove empty tasks
            barrier_entry["task_list"] = list(filter(None, barrier_entry["task_list"]))

            if barrier_entry["task_list"]:
                task_list.append(barrier_entry)

        # Append mentions tasks to existing barrier task list, or create new barrier
        # entries for un-owned barriers
        task_list = self.append_mentions_tasks(user, task_list)

        # Paginate
        paginator = Paginator(task_list, 3)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        return Response(
            status=status.HTTP_200_OK,
            data={"results": page_obj.object_list, "count": len(task_list)},
        )

    def check_publishing_overdue(self, barrier):
        # Get publishing deadline difference for public_barrier related tasks/updates
        # Only set publishing deadlines for barriers in either ALLOWED, APPROVAL_PENDING or PUBLISHING_PENDING status
        if (
            barrier.public_barrier.public_view_status in [20, 70, 30]
            and barrier.public_barrier.set_to_allowed_on
        ):
            publish_deadline = dateutil.parser.parse(
                barrier.public_barrier.set_to_allowed_on.strftime("%m/%d/%Y")
            ) + timedelta(days=30)
            diff = publish_deadline - self.todays_date.replace(tzinfo=None)
            # Set variables to track if barrier is overdue and by how much
            self.publishing_overdue = True if diff.days <= 0 else False
            self.publish_deadline = publish_deadline.strftime("%d %B %Y")

    def set_date_of_third_friday(self):
        # Get the third friday of the month, skip if we've already calculated
        if not self.third_friday_date or not self.first_of_month_date:
            self.first_of_month_date = self.todays_date.replace(day=1)
            # Weekday in int format, 0-6 representing each day
            first_day = self.first_of_month_date.weekday()
            # Add 3 weeks of days if the first is a sat or sun (and nearest friday is last month)
            friday_modifier = 14 if first_day < 4 else 21
            # Add the difference to the nearest friday to 1 then apply friday modifier
            third_friday_day = 1 + (4 - first_day) + friday_modifier
            self.third_friday_date = self.todays_date.replace(day=third_friday_day)

    def get_user_barrier_relations(self, user, user_groups, barrier):
        # Only barrier owners should get notifications for public barrier editing
        barrier_team_members = barrier.barrier_team.all()

        is_owner = False
        is_approver = False
        is_publisher = False

        for team_user in barrier_team_members:
            if team_user.user_id == user.id and team_user.role == "Owner":
                is_owner = True

        for group in user_groups:
            if group.name == "Public barrier approver":
                is_approver = True
            if group.name == "Publisher":
                is_publisher = True

        return (is_owner, is_approver, is_publisher)

    def check_public_barrier_editor_tasks(self, barrier):
        if barrier.public_barrier.public_view_status == 20:
            if barrier.public_barrier.title and barrier.public_barrier.summary:
                # general user needs to send barrier to approver completed detail
                # logic trigger: barrier.public_barrier.public_view_status == 'ALLOWED'
                #   and (barrier.public_barrier.public_title or barrier.public_barrier.public_summary) and not overdue

                # general user needs to send barrier to approver completed detail and overdue
                # logic trigger: barrier.public_barrier.public_view_status == 'ALLOWED'
                #   and (barrier.public_barrier.public_title or barrier.public_barrier.public_summary) and overdue
                if self.publishing_overdue:
                    return {
                        "tag": "OVERDUE REVIEW",
                        "message": [
                            "Submit for clearance checks and GOV.UK publication approval",
                            f"by {self.publish_deadline}.",
                        ],
                        "task_url": "barriers:public_barrier_detail",
                        "link_text": "Submit for clearance checks and GOV.UK publication approval",
                    }
                else:
                    return {
                        "tag": "PUBLICATION REVIEW",
                        "message": [
                            "Submit for clearance checks and GOV.UK publication approval",
                            f"by {self.publish_deadline}.",
                        ],
                        "task_url": "barriers:public_barrier_detail",
                        "link_text": "Submit for clearance checks and GOV.UK publication approval",
                    }
            elif not barrier.public_barrier.title or not barrier.public_barrier.summary:
                # general user needs to send barrier to approver missing detail
                # logic trigger: barrier.public_barrier.public_view_status == 'ALLOWED'
                #   and (not barrier.public_barrier.public_title or not barrier.public_barrier.public_summary)
                #   and not overdue

                # general user needs to send barrier to approver missing detail and overdue
                # logic trigger: barrier.public_barrier.public_view_status == 'ALLOWED'
                #   and (not barrier.public_barrier.public_title or not barrier.public_barrier.public_summary)
                #   and overdue
                if self.publishing_overdue:
                    return {
                        "tag": "OVERDUE REVIEW",
                        "message": [
                            "Add a public title and summary",
                            "to this barrier before it can be approved.",
                            f"This needs to be done by {self.publish_deadline}.",
                        ],
                        "task_url": "barriers:public_barrier_detail",
                        "link_text": "Add a public title and summary",
                    }
                else:
                    return {
                        "tag": "PUBLICATION REVIEW",
                        "message": [
                            "Add a public title and summary",
                            "to this barrier before it can be approved.",
                            f"This needs to be done by {self.publish_deadline}.",
                        ],
                        "task_url": "barriers:public_barrier_detail",
                        "link_text": "Add a public title and summary",
                    }

    def check_public_barrier_approver_tasks(self, barrier):
        # approver needs to approve barrier
        # logic trigger: barrier.public_barrier.public_view_status == 'APPROVAL_PENDING' and not overdue

        # approver needs to approve barrier overdue
        # logic trigger: barrier.public_barrier.public_view_status == 'APPROVAL_PENDING' and overdue
        if barrier.public_barrier.public_view_status == 70:
            if self.publishing_overdue:
                return {
                    "tag": "OVERDUE REVIEW",
                    "message": [
                        "Approve this barrier",
                        f"for publication and complete clearance checks by {self.publish_deadline}.",
                        "It can then be submitted to the GOV.UK content team.",
                    ],
                    "task_url": "barriers:public_barrier_detail",
                    "link_text": "Approve this barrier",
                }
            else:
                return {
                    "tag": "PUBLICATION REVIEW",
                    "message": [
                        "Approve this barrier",
                        f"for publication and complete clearance checks by {self.publish_deadline}.",
                        "It can then be submitted to the GOV.UK content team.",
                    ],
                    "task_url": "barriers:public_barrier_detail",
                    "link_text": "Approve this barrier",
                }

    def check_public_barrier_publisher_tasks(self, barrier):
        # publisher needs to publish barrier
        # logic trigger: barrier.public_barrier.public_view_status == 'PUBLISHING_PENDING' and not overdue

        # publisher needs to publish barrier overdue
        # logic trigger: barrier.public_barrier.public_view_status == 'PUBLISHING_PENDING' and overdue

        # Publisher needs to publish barrier
        if barrier.public_barrier.public_view_status == 30:
            if self.publishing_overdue:
                return {
                    "tag": "OVERDUE REVIEW",
                    "message": [
                        "Complete GOV.UK content checks",
                        f"by {self.publish_deadline}.",
                    ],
                    "task_url": "barriers:public_barrier_detail",
                    "link_text": "Complete GOV.UK content checks",
                }
            else:
                return {
                    "tag": "PUBLICATION REVIEW",
                    "message": [
                        "Complete GOV.UK content checks",
                        f"by {self.publish_deadline}.",
                    ],
                    "task_url": "barriers:public_barrier_detail",
                    "link_text": "Complete GOV.UK content checks",
                }

    def check_missing_barrier_details(self, barrier):
        missing_details_task_list = []
        if barrier.status in [1, 2, 3]:
            # hs code missing
            # logic trigger: (barrier.status == 'OPEN' or barrier.status == 'RESOLVED IN PART')
            #   and 'goods' in barrier.export_types and barrier.hs_code is null
            if (
                barrier.export_types.filter(name="goods")
                and not barrier.commodities.all()
            ):
                missing_details_task_list.append(
                    {
                        "tag": "ADD INFORMATION",
                        "message": ["Add an HS code to this barrier."],
                        "task_url": "barriers:edit_commodities",
                        "link_text": "Add an HS code to this barrier.",
                    }
                )

            # other government department missing
            # logic trigger: (barrier.status== 'OPEN' or barrier.status == 'RESOLVED IN PART')
            #   and barrier.government_organisations is null
            if not barrier.government_organisations:
                missing_details_task_list.append(
                    {
                        "tag": "ADD INFORMATION",
                        "message": [
                            "Check and add any other government departments (OGDs)",
                            "involved in the resolution of this barrier.",
                        ],
                        "task_url": "barriers:edit_gov_orgs",
                        "link_text": "Check and add any other government departments (OGDs)",
                    }
                )

            # missing delivery confidence for barriers with estimated resolution date in financial year
            # logic trigger: (barrier.status == 'OPEN' or barrier.status == 'RESOLVED IN PART')
            #   and barrier.progress_updates is null and barrier.estimated_resolution_date > financial_year_start
            #   and barrier.estimated_resolution_date < financial_year_end
            if barrier.estimated_resolution_date:

                if self.todays_date < datetime(self.todays_date.year, 4, 6).replace(
                    tzinfo=timezone.utc
                ):
                    # Financial year runs from previous year to current
                    start_year_value = self.todays_date.year - 1
                    end_year_value = self.todays_date.year
                else:
                    # Financial year runs from current year to next
                    start_year_value = self.todays_date.year
                    end_year_value = self.todays_date.year + 1

                financial_year_start = datetime.strptime(
                    f"06/04/{start_year_value} 00:00:00", "%d/%m/%Y %H:%M:%S"
                )
                financial_year_end = datetime.strptime(
                    f"06/04/{end_year_value} 00:00:00", "%d/%m/%Y %H:%M:%S"
                )
                estimated_resolution_datetime = datetime(
                    barrier.estimated_resolution_date.year,
                    barrier.estimated_resolution_date.month,
                    barrier.estimated_resolution_date.day,
                )

                if (
                    not barrier.progress_updates.all()
                    and estimated_resolution_datetime > financial_year_start
                    and estimated_resolution_datetime < financial_year_end
                ):
                    missing_details_task_list.append(
                        {
                            "tag": "ADD INFORMATION",
                            "message": [
                                "Add your delivery confidence",
                                "to this barrier.",
                            ],
                            "task_url": "barriers:add_progress_update",
                            "link_text": "Add your delivery confidence",
                        }
                    )

        return missing_details_task_list

    def check_estimated_resolution_date_tasks(self, user, barrier):
        estimated_resolution_date_task_list = []
        if barrier.status in [1, 2, 3]:

            # outdated estimated resolution date
            # logic trigger: (barrier.status == "OPEN" or barrier.status == "RESOLVED IN PART")
            #   and barrier.estimated_resolution_date < todays_date
            if barrier.estimated_resolution_date:
                estimated_resolution_datetime = datetime.combine(
                    barrier.estimated_resolution_date, time(00, 00, 00)
                )
                if estimated_resolution_datetime < self.todays_date.replace(
                    tzinfo=None
                ):
                    estimated_resolution_date_task_list.append(
                        {
                            "tag": "CHANGE OVERDUE",
                            "message": [
                                "Review the estimated resolution date",
                                f"as it is currently listed as {barrier.estimated_resolution_date},",
                                "which is in the past.",
                            ],
                            "task_url": "barriers:edit_estimated_resolution_date",
                            "link_text": "Review the estimated resolution date",
                        }
                    )

            if hasattr(barrier.barrier_team.filter(role="Owner").first(), "user_id"):
                if user.id == barrier.barrier_team.filter(role="Owner").first().user_id:
                    # estimated resolution date missing for high priorities
                    # stored logic_trigger: "(barrier.is_top_priority or barrier.priority_level == 'overseas delivery')
                    #   and not barrier.estimated_resolution_date and
                    #   (barrier.status == 'OPEN' or barrier.status == 'RESOLVED IN PART')
                    if (
                        barrier.is_top_priority or barrier.priority_level == "OVERSEAS"
                    ) and not barrier.estimated_resolution_date:
                        estimated_resolution_date_task_list.append(
                            {
                                "tag": "ADD DATE",
                                "message": [
                                    "Add an estimated resolution date",
                                    "to this PB100 barrier.",
                                ],
                                "task_url": "barriers:edit_estimated_resolution_date",
                                "link_text": "Add an estimated resolution date",
                            }
                        )

                    # progress update estimated resolution date outdated
                    # stored logic_trigger: "barrier.is_top_priority
                    #   and (barrier.status == "OPEN" or barrier.status == "RESOLVED IN PART"
                    #   and latest_update.modified_on < progress_update_expiry_date"
                    latest_update = barrier.latest_progress_update
                    progress_update_expiry_date = self.todays_date - timedelta(days=180)
                    if latest_update and (
                        barrier.is_top_priority
                        and latest_update.modified_on.replace(tzinfo=None)
                        < datetime(
                            progress_update_expiry_date.year,
                            progress_update_expiry_date.month,
                            progress_update_expiry_date.day,
                        ).replace(tzinfo=None)
                    ):
                        readable_modified_date = latest_update.modified_on.strftime(
                            "%d %B %Y"
                        )
                        estimated_resolution_date_task_list.append(
                            {
                                "tag": "REVIEW DATE",
                                "message": [
                                    "Check the estimated resolution date",
                                    f"as it has not been reviewed since {readable_modified_date}.",
                                ],
                                "task_url": "barriers:edit_estimated_resolution_date",
                                "link_text": "Check the estimated resolution date",
                            }
                        )

        return estimated_resolution_date_task_list

    def check_progress_update_tasks(self, barrier):
        progress_update_task_list = []
        progress_update = barrier.latest_progress_update

        # monthly progress update upcoming
        # is_top_priority = true
        #   AND (progress_update_date IS BETWEEN 01 - current month - current year and 3rd Friday of month)
        #   AND status = OPEN OR status = RESOLVED IN PART

        # monthly progress update overdue
        # is_top_priority = true
        #   AND (progress_update_date NOT BETWEEN 01 - current month - current year and 3rd Friday of month)
        #   AND status = OPEN OR status = RESOLVED IN PART
        if barrier.is_top_priority:
            self.set_date_of_third_friday()
            if not progress_update or (
                progress_update.modified_on < self.first_of_month_date
                and self.todays_date < self.third_friday_date
            ):
                # Latest update was last month and the current date is before the third friday (the due date)
                # Barrier needs an upcoming task added
                progress_update_task_list.append(
                    {
                        "tag": "PROGRESS UPDATE DUE",
                        "message": [
                            "Add a monthly progress update",
                            f"to this PB100 barrier by {self.third_friday_date.strftime('%d %B %Y')}.",
                        ],
                        "task_url": "barriers:add_progress_update",
                        "link_text": "Add a monthly progress update",
                    }
                )
            elif (
                progress_update.modified_on < self.first_of_month_date
                and self.todays_date > self.third_friday_date
            ):
                # Latest update was last month and the current date is past the third friday (the due date)
                # Barrier needs an overdue task added
                progress_update_task_list.append(
                    {
                        "tag": "OVERDUE PROGRESS UPDATE",
                        "message": [
                            "Add a monthly progress update",
                            f"to this PB100 barrier by {self.third_friday_date.strftime('%d %B %Y')}.",
                        ],
                        "task_url": "barriers:add_progress_update",
                        "link_text": "Add a monthly progress update",
                    }
                )

            # overdue next step for pb100 barriers
            # is_top_priority = true  AND public.market_access_trade_barrier_next_steps (status = IN_PROGRESS)
            #   AND public.market_access_trade_barrier_next_steps(completion_date<current date)
            #   AND (status = OPEN OR status = RESOLVED IN PART)
            for step in barrier.next_steps_items.all():
                if (
                    step.status == "IN_PROGRESS"
                    and step.completion_date < datetime.date(self.todays_date)
                ):
                    # Calculate the difference in months
                    difference = (
                        step.completion_date.year - self.todays_date.year
                    ) * 12 + (step.completion_date.month - self.todays_date.month)
                    progress_update_task_list.append(
                        {
                            "tag": "REVIEW NEXT STEP",
                            "message": [
                                "Review the next steps",
                                f"as they have not been checked since {step.completion_date}.",
                            ],
                            "task_url": "barriers:list_next_steps",
                            "link_text": "Review the next steps",
                        }
                    )

        # quarterly overseas delivery update
        # priority_level = overseas_delivery AND progress_update_date > 90 days
        #   AND status = OPEN OR status = RESOLVED IN PART
        if barrier.priority_level == "OVERSEAS":
            update_date_limit = self.todays_date - timedelta(days=90)
            if not progress_update or (progress_update.modified_on < update_date_limit):
                progress_update_task_list.append(
                    {
                        "tag": "PROGRESS UPDATE DUE",
                        "message": [
                            "Add a quarterly progress update",
                            "to this overseas delivery barrier.",
                        ],
                        "task_url": "barriers:add_progress_update",
                        "link_text": "Add a quarterly progress update",
                    }
                )

        # quarterly programme fund update
        # tag = 'programme fund - facilative regional fund'
        #   AND programme_fund_progress_update_date > 90 days old AND status = OPEN OR status = RESOLVED IN PART
        tags_list = [tag.title for tag in barrier.tags.all()]
        if "Programme Fund - Facilitative Regional" in tags_list:
            update_date_limit = self.todays_date - timedelta(days=90)
            if not barrier.latest_programme_fund_progress_update or (
                barrier.latest_programme_fund_progress_update.modified_on
                < update_date_limit
            ):
                progress_update_task_list.append(
                    {
                        "tag": "PROGRESS UPDATE DUE",
                        "message": ["Add a programme fund update", "to this barrier."],
                        "task_url": "barriers:add_programme_fund_progress_update",
                        "link_text": "Add a programme fund update",
                    }
                )

        return progress_update_task_list

    def append_mentions_tasks(self, user, barrier_task_list):
        # Get the mentions for the given user
        user_mentions = Mention.objects.filter(
            recipient=user,
            created_on__date__gte=(datetime.now() - timedelta(days=30)),
        ).prefetch_related(
            "barrier",
        )

        mention_users = User.objects.filter(
            id__in=[mention.created_by_id for mention in user_mentions]
        ).values("first_name", "last_name", "pk")
        user_lookup = {str(u["pk"]): u for u in mention_users}

        for mention in user_mentions:
            mentioner = user_lookup[str(mention.created_by_id)]
            mention_task = {
                "tag": "REVIEW COMMENT",
                "message": [
                    "Reply to the comment",
                    f"{mentioner['first_name']} {mentioner['last_name']} mentioned you in on",
                    f"{mention.created_on.strftime('%d %B %Y')}.",
                ],
                "task_url": "barriers:barrier_detail",
                "link_text": "Reply to the comment",
            }

            mention_appended = False
            for barrier_task in barrier_task_list:
                if barrier_task["barrier_id"] == mention.barrier.id:
                    barrier_task["task_list"].append(mention_task)
                    mention_appended = True
                    break

            # If we have passed the loop and the mention has not been assigned, we need a new barrier added
            if not mention_appended:
                barrier_entry = self.create_barrier_entry(mention.barrier)
                barrier_entry["task_list"].append(mention_task)
                barrier_task_list.append(barrier_entry)

        return barrier_task_list

    def create_barrier_entry(self, barrier):

        # Account for possible None values on barrier
        first_name = (
            "Unknown" if not barrier.modified_by else barrier.modified_by.first_name
        )
        last_name = "" if not barrier.modified_by else barrier.modified_by.last_name
        modified_on = (
            "Unknown"
            if not barrier.modified_on
            else barrier.modified_on.strftime("%d %B %Y")
        )

        barrier_entry = {
            "barrier_id": str(barrier.id),
            "barrier_code": barrier.code,
            "barrier_title": barrier.title,
            "modified_by": first_name + " " + last_name,
            "modified_on": modified_on,
            "task_list": [],
        }

        return barrier_entry
