import factory

from api.action_plans.models import (
    ActionPlan,
    ActionPlanMilestone,
    ActionPlanTask,
    Stakeholder,
)


class ActionPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActionPlan


class ActionPlanMilestoneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActionPlanMilestone


class ActionPlanTaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActionPlanTask


class ActionPlanStakeholderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Stakeholder
