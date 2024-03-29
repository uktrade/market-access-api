import urllib.parse

from django.conf import settings
from django.http import Http404
from notifications_python_client.notifications import NotificationsAPIClient
from rest_framework import status, viewsets
from rest_framework.response import Response

from api.action_plans.serializers import (
    ActionPlanMilestoneSerializer,
    ActionPlanSerializer,
    ActionPlanStakeholderSerializer,
    ActionPlanTaskSerializer,
)
from api.barriers.models import Barrier
from api.collaboration.models import TeamMember
from api.user.helpers import get_django_user_by_sso_user_id

from .models import ActionPlan, ActionPlanMilestone, ActionPlanTask, Stakeholder


class ActionPlanViewSet(viewsets.ModelViewSet):

    queryset = ActionPlan.objects.all()
    serializer_class = ActionPlanSerializer

    lookup_field = "barrier"

    def notify(self, django_user, barrier):
        barrier_obj = Barrier.objects.get(id=barrier)
        client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
        barrier_url = urllib.parse.urljoin(
            settings.FRONTEND_DOMAIN, f"/barriers/{barrier}/action_plan"
        )
        client.send_email_notification(
            email_address=django_user.email,
            template_id=settings.NOTIFY_ACTION_PLAN_USER_SET_AS_OWNER_ID,
            personalisation={
                "first_name": django_user.first_name,
                "mentioned_by": f"{django_user.first_name} {django_user.last_name}",
                "barrier_number": barrier_obj.code,
                "barrier_name": barrier_obj.title,
                "barrier_url": barrier_url,
            },
        )

    def retrieve(self, request, barrier, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404 as e:
            barrier = Barrier.objects.get(pk=barrier)
            instance = ActionPlan(barrier=barrier)
            instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, barrier, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        sso_user_id = self.request.data.get("owner")
        django_user = None
        if sso_user_id:
            django_user = get_django_user_by_sso_user_id(sso_user_id)
            data = {**request.data, "owner": django_user.id}
        else:
            data = request.data

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if django_user:
            self.notify(django_user, barrier)
            barrier = Barrier.objects.get(pk=barrier)
            if not barrier.barrier_team.filter(user=django_user).exists():
                TeamMember.objects.create(
                    barrier=barrier,
                    user=django_user,
                    role=TeamMember.CONTRIBUTOR,
                )

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class ActionPlanMilestoneViewSet(viewsets.ModelViewSet):

    queryset = ActionPlanMilestone.objects.all()
    serializer_class = ActionPlanMilestoneSerializer

    lookup_field = "id"

    def create(self, request, barrier, *args, **kwargs):
        action_plan = ActionPlan.objects.get(barrier_id=str(barrier))

        serializer = self.get_serializer(
            data={"action_plan": action_plan.id, **request.data}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ActionPlanTaskViewSet(viewsets.ModelViewSet):

    queryset = ActionPlanTask.objects.all()
    serializer_class = ActionPlanTaskSerializer

    lookup_field = "id"

    def notify(self, django_user, barrier):
        barrier_obj = Barrier.objects.get(id=barrier)
        client = NotificationsAPIClient(settings.NOTIFY_API_KEY)
        barrier_url = urllib.parse.urljoin(
            settings.FRONTEND_DOMAIN, f"/barriers/{barrier}/action_plan"
        )
        client.send_email_notification(
            email_address=django_user.email,
            template_id=settings.NOTIFY_ACTION_PLAN_NOTIFCATION_ID,
            personalisation={
                "first_name": django_user.first_name,
                "mentioned_by": f"{django_user.first_name} {django_user.last_name}",
                "barrier_number": barrier_obj.code,
                "barrier_name": barrier_obj.title,
                "barrier_url": barrier_url,
            },
        )

    def update(self, request, barrier, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        sso_user_id = self.request.data.get("assigned_to")
        django_user = None
        if sso_user_id:
            django_user = get_django_user_by_sso_user_id(sso_user_id)
            data = {**request.data, "assigned_to": django_user.id}
        else:
            data = request.data

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if django_user:
            self.notify(django_user, barrier)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def create(self, request, barrier, *args, **kwargs):
        action_plan = ActionPlan.objects.get(barrier_id=str(barrier))

        sso_user_id = self.request.data.get("assigned_to")
        # sso_user_id = assigned_to["profile"]["sso_user_id"]
        django_user = get_django_user_by_sso_user_id(sso_user_id)

        serializer = self.get_serializer(
            data={**request.data, "assigned_to": django_user.id}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        self.notify(django_user, barrier)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ActionPlanStakeholderViewSet(viewsets.ModelViewSet):
    queryset = Stakeholder.objects.all()
    serializer_class = ActionPlanStakeholderSerializer

    lookup_field = "id"

    def action_plan_from_barrier_kwarg(self, kwargs):
        barrier_id = kwargs.pop("barrier")
        action_plan = ActionPlan.objects.get(barrier_id=str(barrier_id))
        return action_plan

    def create(self, request, *args, **kwargs):
        action_plan = self.action_plan_from_barrier_kwarg(kwargs)
        request.data["action_plan"] = action_plan.pk
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        action_plan = self.action_plan_from_barrier_kwarg(kwargs)
        request.data["action_plan"] = action_plan.pk
        return super().update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        action_plan = self.action_plan_from_barrier_kwarg(kwargs)
        request.data["action_plan"] = action_plan.pk
        return super().destroy(request, *args, **kwargs)
