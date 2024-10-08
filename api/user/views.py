import logging
from datetime import datetime, time, timedelta, timezone
from http import HTTPStatus

import dateutil.parser
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from hawkrest import HawkAuthentication
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.barriers.models import Barrier
from api.interactions.models import Mention
from api.user.helpers import get_django_user_by_sso_user_id
from api.user.models import (
    Profile,
    UserActvitiyLog,
    get_my_barriers_saved_search,
    get_team_barriers_saved_search,
)
from api.user.serializers import (
    GroupSerializer,
    SavedSearchSerializer,
    UserActvitiyLogSerializer,
    UserDetailSerializer,
    UserListSerializer,
    WhoAmISerializer,
)

UserModel = get_user_model()
logger = logging.getLogger(__name__)


@api_view(["GET", "POST", "PATCH"])
@permission_classes([])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    try:
        token = request.auth.token
    except AttributeError:
        logger.info(f"Unauthorized missing or invalid token: {request.auth}")
        return HttpResponse(
            "Unauthorized missing or invalid token", status=HTTPStatus.UNAUTHORIZED
        )

    context = {"token": token}
    serializer = WhoAmISerializer(request.user, context=context)

    if request.method == "PATCH":
        req_profile = request.data.get("user_profile", None)
        if req_profile:
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                Profile.objects.create(user=request.user)

            request.user.profile.user_profile = req_profile
            request.user.profile.save()
            request.user.save()

    if request.method == "POST":
        return Response(data=request.data)
    return Response(data=serializer.data)


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserDetailSerializer

    def get_object(self):
        sso_user_id = self.kwargs.get("sso_user_id")
        if sso_user_id:
            return get_django_user_by_sso_user_id(sso_user_id)
        return super().get_object()


class SavedSearchList(generics.ListCreateAPIView):
    serializer_class = SavedSearchSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name"]

    def get_queryset(self):
        return self.request.user.saved_searches.all()


class SavedSearchDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SavedSearchSerializer

    def get_object(self):
        if self.kwargs.get("id") == "my-barriers":
            return get_my_barriers_saved_search(self.request.user)

        if self.kwargs.get("id") == "team-barriers":
            return get_team_barriers_saved_search(self.request.user)

        return super().get_object()

    def get_queryset(self):
        return self.request.user.saved_searches.all()


class GroupList(generics.ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupDetail(generics.RetrieveAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class UserList(generics.ListAPIView):
    queryset = UserModel.objects.all()
    serializer_class = UserListSerializer
    filter_backends = [OrderingFilter, SearchFilter, DjangoFilterBackend]
    ordering_fields = ("last_name", "first_name", "email")
    ordering = ("first_name", "last_name", "email", "role")
    search_fields = ("first_name", "last_name", "email")
    filterset_fields = [
        "groups__id",
    ]

    def list(self, request, *args, **kwargs):
        self.paginator.default_limit = 10
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(role=F("groups__name"))
            .distinct("last_name", "first_name", "email")
            # distinct needs to match ordering values
            # because Postgres says so
        )


class UserActivityLogList(generics.ListAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    serializer_class = UserActvitiyLogSerializer

    def get_queryset(self):
        return UserActvitiyLog.objects.order_by("-event_time").all()


class DashboardUserTasksView(generics.ListAPIView):
    """
    Returns list of dashboard next steps, tasks and progress updates
    related to barriers where a given user is either owner or
    collaborator.
    """

    # Set variables used in date related calculations
    todays_date = datetime.now(timezone.utc)
    publishing_overdue = False
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
            .order_by("modified_on")[:1000]
            .select_related("public_barrier")
            .prefetch_related(
                "progress_updates",
                "barrier_team",
                "barrier_commodities",
                "next_steps_items",
                "tags",
                "export_types",
            )
        )

        # Initialise task list
        task_list = []

        # With the list of barriers the user could potentially see, we now need to build a list of
        # tasks derived from conditions the barriers in the list are in.
        for barrier in users_barriers:
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
                    task_list.append(publishing_editor_task)

            # Only add public barrier approver tasks for users with that role
            if is_approver:
                publishing_approver_task = self.check_public_barrier_approver_tasks(
                    barrier
                )
                task_list.append(publishing_approver_task)

            # Only add public barrier publisher tasks for users with that role
            if is_publisher:
                publishing_publisher_task = self.check_public_barrier_publisher_tasks(
                    barrier
                )
                task_list.append(publishing_publisher_task)

            if barrier.status in [1, 2, 3]:
                progress_update_tasks = self.check_progress_update_tasks(barrier)
                task_list += progress_update_tasks

            missing_barrier_tasks = self.check_missing_barrier_details(barrier)
            task_list += missing_barrier_tasks

            estimated_resolution_date_tasks = (
                self.check_estimated_resolution_date_tasks(user, barrier)
            )
            task_list += estimated_resolution_date_tasks

        mentions_tasks = self.check_mentions_tasks(user)
        # Combine list of tasks with list of mentions
        task_list += mentions_tasks

        # Remove empty tasks
        filtered_task_list = list(filter(None, task_list))

        # Paginate
        paginator = Paginator(filtered_task_list, 5)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        return Response(
            status=status.HTTP_200_OK,
            data={"results": page_obj.object_list, "count": len(filtered_task_list)},
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
                        "barrier_code": barrier.code,
                        "barrier_title": barrier.title,
                        "barrier_id": barrier.id,
                        "tag": "OVERDUE REVIEW",
                        "message": f"""Submit this barrier for a review and clearance checks before the GOV.UK content
                        team to publish it. This needs to be done within {self.countdown} days.""",
                    }
                else:
                    return {
                        "barrier_code": barrier.code,
                        "barrier_title": barrier.title,
                        "barrier_id": barrier.id,
                        "tag": "PUBLICATION REVIEW",
                        "message": f"""Submit this barrier for a review and clearance checks before the
                        GOV.UK content team to publish it. This needs to be done within {self.countdown} days.""",
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
                        "barrier_code": barrier.code,
                        "barrier_title": barrier.title,
                        "barrier_id": barrier.id,
                        "tag": "OVERDUE REVIEW",
                        "message": f"""Add a public title and summary to this barrier before it can be
                        approved. This needs to be done within {self.countdown} days""",
                    }
                else:
                    return {
                        "barrier_code": barrier.code,
                        "barrier_title": barrier.title,
                        "barrier_id": barrier.id,
                        "tag": "PUBLICATION REVIEW",
                        "message": f"""Add a public title and summary to this barrier before it can be
                        approved. This needs to be done within {self.countdown} days""",
                    }

    def check_public_barrier_approver_tasks(self, barrier):
        # approver needs to approve barrier
        # logic trigger: barrier.public_barrier.public_view_status == 'APPROVAL_PENDING' and not overdue

        # approver needs to approve barrier overdue
        # logic trigger: barrier.public_barrier.public_view_status == 'APPROVAL_PENDING' and overdue
        if barrier.public_barrier.public_view_status == 70:
            if self.publishing_overdue:
                return {
                    "barrier_code": barrier.code,
                    "barrier_title": barrier.title,
                    "barrier_id": barrier.id,
                    "tag": "OVERDUE REVIEW",
                    "message": f"""Review and check this barrier for clearances before it can be submitted
                    to the content team. This needs to be done within {self.countdown} days""",
                }
            else:
                return {
                    "barrier_code": barrier.code,
                    "barrier_title": barrier.title,
                    "barrier_id": barrier.id,
                    "tag": "PUBLICATION REVIEW",
                    "message": f"""Review and check this barrier for clearances before it can be submitted
                    to the content team. This needs to be done within {self.countdown} days""",
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
                    "barrier_code": barrier.code,
                    "barrier_title": barrier.title,
                    "barrier_id": barrier.id,
                    "tag": "OVERDUE REVIEW",
                    "message": f"""This barrier has been approved. Complete the final content checks
                    and publish it. This needs to be done within {self.countdown} days""",
                }
            else:
                return {
                    "barrier_code": barrier.code,
                    "barrier_title": barrier.title,
                    "barrier_id": barrier.id,
                    "tag": "PUBLICATION REVIEW",
                    "message": f"""This barrier has been approved. Complete the final content checks
                    and publish it. This needs to be done within {self.countdown} days""",
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
                        "barrier_code": barrier.code,
                        "barrier_title": barrier.title,
                        "barrier_id": barrier.id,
                        "tag": "ADD INFORMATION",
                        "message": """This barrier relates to the export of goods but it does not contain
                        any HS commodity codes. Check and add the codes now.""",
                    }
                )

            # other government department missing
            # logic trigger: (barrier.status== 'OPEN' or barrier.status == 'RESOLVED IN PART')
            #   and barrier.government_organisations is null
            if not barrier.government_organisations:
                missing_details_task_list.append(
                    {
                        "barrier_code": barrier.code,
                        "barrier_title": barrier.title,
                        "barrier_id": barrier.id,
                        "tag": "ADD INFORMATION",
                        "message": """This barrier is not currently linked with any other government
                        departments (OGD) Check and add any relevant OGDs involved in the
                        resolution of this barrier""",
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
                            "barrier_code": barrier.code,
                            "barrier_title": barrier.title,
                            "barrier_id": barrier.id,
                            "tag": "ADD INFORMATION",
                            "message": """This barrier does not have information on how confident you feel
                            about resolving it this financial year. Add the delivery confidence now.""",
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
                            "barrier_code": barrier.code,
                            "barrier_title": barrier.title,
                            "barrier_id": barrier.id,
                            "tag": "CHANGE OVERDUE",
                            "message": """The estimated resolution date of this barrier is now in the
                            past. Review and add a new date now.""",
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
                                "barrier_code": barrier.code,
                                "barrier_title": barrier.title,
                                "barrier_id": barrier.id,
                                "tag": "ADD DATE",
                                "message": """As this is a priority barrier you need to add an
                                estimated resolution date.""",
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
                        difference = (
                            latest_update.modified_on.year - self.todays_date.year
                        ) * 12 + (
                            latest_update.modified_on.month - self.todays_date.month
                        )
                        estimated_resolution_date_task_list.append(
                            {
                                "barrier_code": barrier.code,
                                "barrier_title": barrier.title,
                                "barrier_id": barrier.id,
                                "tag": "REVIEW DATE",
                                "message": f"""This barriers estimated resolution date has not
                                been updated in {abs(difference)} months. Check if this date is still accurate.""",
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
                        "barrier_code": barrier.code,
                        "barrier_title": barrier.title,
                        "barrier_id": barrier.id,
                        "tag": "PROGRESS UPDATE DUE",
                        "message": f"""This is a PB100 barrier. Add a monthly progress update
                        by {self.third_friday_date.strftime("%d-%m-%y")}""",
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
                        "barrier_code": barrier.code,
                        "barrier_title": barrier.title,
                        "barrier_id": barrier.id,
                        "tag": "OVERDUE PROGRESS UPDATE",
                        "message": f"""This is a PB100 barrier. Add a monthly progress update
                        by {self.third_friday_date.strftime("%d-%m-%y")}""",
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
                            "barrier_code": barrier.code,
                            "barrier_title": barrier.title,
                            "barrier_id": barrier.id,
                            "tag": "REVIEW NEXT STEP",
                            "message": f"""The next step for this barrier has not been reviewed
                            for more than {abs(difference)} months. Review the next step now.""",
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
                        "barrier_code": barrier.code,
                        "barrier_title": barrier.title,
                        "barrier_id": barrier.id,
                        "tag": "PROGRESS UPDATE DUE",
                        "message": """This is an overseas delivery barrier but there has not been
                        an update for over 3 months. Add a quarterly progress update now.""",
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
                        "barrier_code": barrier.code,
                        "barrier_title": barrier.title,
                        "barrier_id": barrier.id,
                        "tag": "PROGRESS UPDATE DUE",
                        "message": """There is an active programme fund for this barrier but
                        there has not been an update for over 3 months. Add a programme fund update now.""",
                    }
                )

        return progress_update_task_list

    def check_mentions_tasks(self, user):
        mention_tasks_list = []
        # Get the mentions for the given user
        user_mentions = Mention.objects.filter(
            recipient=user,
            created_on__date__gte=(datetime.now() - timedelta(days=30)),
        )
        for mention in user_mentions:
            # Get name of the mentioner
            mentioner = User.objects.get(id=mention.created_by_id)
            mention_task = {
                "barrier_code": "",
                "barrier_title": "",
                "barrier_id": "",
                "tag": "REVIEW COMMENT",
                "message": f"""{mentioner.first_name} {mentioner.last_name} mentioned you
                in a comment on {mention.created_on.strftime("%d-%m-%y")} and wants you to reply.""",
            }
            mention_tasks_list.append(mention_task)

        return mention_tasks_list
        # Once a mention is clicked on the frontend, make a call to the
        # notification view that will clear the mark the mention as read
        # this should be an existing function called by the frontend
