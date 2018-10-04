from uuid import uuid4

from django.db import models
from django.db.models import Q

from api.metadata.constants import BARRIER_TYPE_CATEGORIES


class GoodsManager(models.Manager):
    """ Manage reports within the model, with status 0 """
    def get_queryset(self):
        return super(GoodsManager, self).get_queryset().filter(Q(category="GOODS") | Q(category="GOODSANDSERVICES"))


class ServicesManager(models.Manager):
    """ Manage barriers within the model, with status not 0 """
    def get_queryset(self):
        return super(ServicesManager, self).get_queryset().filter(Q(category="SERVICES") | Q(category="GOODSANDSERVICES"))

class BarrierType(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid4)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=BARRIER_TYPE_CATEGORIES)

    objects = models.Manager()
    goods = GoodsManager()
    services = ServicesManager()

    def __str__(self):
        return self.title
