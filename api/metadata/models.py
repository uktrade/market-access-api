import json
from uuid import uuid4

from django.db import models
from django.db.models import Q

from api.metadata.constants import BARRIER_TYPE_CATEGORIES


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


class BarrierType(models.Model):
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


class BarrierPriority(models.Model):
    """ Model representing Priority to be set for each Barrier """
    code = models.CharField(max_length=10, null=False, unique=True)
    name = models.CharField(max_length=25)
    order = models.IntegerField(null=False)

    def __repr__(self):
        return self.code

    def __str__(self):
        return self.code

    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4
        )
