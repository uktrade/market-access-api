from api.action_plans.serializers import (
    ActionPlanMilestoneSerializer,
    ActionPlanSerializer,
    ActionPlanTaskSerializer,
)
from api.barriers.models import Barrier
from api.user.helpers import get_django_user_by_sso_user_id
from django.http import Http404
from rest_framework import generics, mixins, status, views, viewsets
from rest_framework.response import Response

from .models import ActionPlan, ActionPlanMilestone, ActionPlanTask


class ActionPlanViewSet(viewsets.ModelViewSet):

    queryset = ActionPlan.objects.all()
    serializer_class = ActionPlanSerializer

    lookup_field = "barrier"

    def retrieve(self, request, barrier, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404 as e:
            barrier = Barrier.objects.get(pk=barrier)
            instance = ActionPlan(barrier=barrier, owner=barrier.created_by)
            instance.save()
        serializer = self.get_serializer(instance)
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        sso_user_id = self.request.data.get("assigned_to")
        if sso_user_id:
            django_user = get_django_user_by_sso_user_id(sso_user_id)
            data = {**request.data, "assigned_to": django_user.id}
        else:
            data = request.data

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

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
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
