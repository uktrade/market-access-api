import logging
from datetime import datetime, time, timedelta

import dateutil.parser
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response

from api.barriers.models import Barrier, BarrierFilterSet
from api.barriers.serializers import BarrierListSerializer
from api.dashboard import service
from api.interactions.models import Mention

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
    countdown = 0
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
            .order_by("-modified_on")[:100]
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
        set_to_allowed_date = barrier.public_barrier.set_to_allowed_on
        if (
            barrier.public_barrier.public_view_status in [20, 70, 30]
            and set_to_allowed_date
        ):
            publish_deadline = dateutil.parser.parse(
                set_to_allowed_date.strftime("%m/%d/%Y")
            ) + timedelta(days=30)
            diff = publish_deadline - self.todays_date.replace(tzinfo=None)
            # Set variables to track if barrier is overdue and by how much
            self.publishing_overdue = True if diff.days <= 0 else False
            self.countdown = 0 if diff.days <= 0 else diff.days
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

        for mention in user_mentions:
            mentioner = User.objects.get(id=mention.created_by_id)
            mention_task = {
                "tag": "REVIEW COMMENT",
                "message": [
                    "Reply to the comment",
                    f"{mentioner.first_name} {mentioner.last_name} mentioned you in on",
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
            "barrier_id": barrier.id,
            "barrier_code": barrier.code,
            "barrier_title": barrier.title,
            "modified_by": first_name + " " + last_name,
            "modified_on": modified_on,
            "task_list": [],
        }

        return barrier_entry
