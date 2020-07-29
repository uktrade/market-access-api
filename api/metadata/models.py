import json

from django.db import models
from django.db.models import Q
from ordered_model.models import OrderedModel

from api.metadata.constants import BARRIER_TYPE_CATEGORIES
from api.core.models import BaseModel


class GoodsManager(models.Manager):
    """ Manage reports within the model, with status 0 """

    def get_queryset(self):
        return (
            super(GoodsManager, self)
            .get_queryset()
            .filter(Q(category="GOODS") | Q(category="GOODSANDSERVICES"))
        )


class ServicesManager(models.Manager):
    """ Manage barriers within the model, with status not 0 """

    def get_queryset(self):
        return (
            super(ServicesManager, self)
            .get_queryset()
            .filter(Q(category="SERVICES") | Q(category="GOODSANDSERVICES"))
        )


class Category(models.Model):
    """
    Model representing type of a barrier
    Each type belongs to one or more categories
    """

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=BARRIER_TYPE_CATEGORIES)

    objects = models.Manager()
    goods = GoodsManager()
    services = ServicesManager()

    def __str__(self):
        return self.title

    # TODO: remove - looks like this is not being used
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class BarrierTag(OrderedModel, BaseModel):
    """
    Model representing tags that can be applied to barriers.
    """
    title = models.CharField(max_length=25, unique=True)
    description = models.CharField(
        blank=True,
        max_length=250,
        help_text="Additional information about the tag to be shown to the end users. (optional)"
    )
    show_at_reporting = models.BooleanField(
        default=False,
        help_text="When set to True the tag is shown as an option during barrier reporting flow."
    )

    def __str__(self):
        return self.title


class BarrierPriority(models.Model):
    """ Model representing Priority to be set for each Barrier """

    code = models.CharField(max_length=10, null=False, unique=True)
    name = models.CharField(max_length=25)
    order = models.IntegerField(null=False)

    def __repr__(self):
        return self.code

    def __str__(self):
        return self.code

    # TODO: remove - looks like this is not being used
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
