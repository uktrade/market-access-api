import json

from django.conf import settings
from django.shortcuts import render

from hawkrest import HawkAuthentication

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .utils import import_api_results

from api.metadata.constants import (
    ADV_BOOLEAN,
    BARRIER_SOURCE,
    BARRIER_STATUS,
    BARRIER_TYPE_CATEGORIES,
    BARRIER_CHANCE_OF_SUCCESS,
    BARRIER_INTERACTION_TYPE,
    ESTIMATED_LOSS_RANGE,
    GOVT_RESPONSE,
    PROBLEM_STATUS_TYPES,
    PUBLISH_RESPONSE,
    REPORT_STATUS,
    STAGE_STATUS,
    SUPPORT_TYPE,
    TIMELINE_EVENTS,
)
from api.metadata.models import (
    BarrierType,
    BarrierPriority
)
from api.barriers.models import Stage


class MetadataView(generics.GenericAPIView):
    if settings.HAWK_ENABLED:
        authentication_classes = (HawkAuthentication,)
        permission_classes = (IsAuthenticated,)
    else:
        authentication_classes = ()
        permission_classes = ()

    def get_barrier_types(self):
        barrier_goods = [
            {
                "id": barrier_type.id,
                "title": barrier_type.title,
                "description": barrier_type.description,
                "category": "GOODS",
            }
            for barrier_type in BarrierType.goods.all()
        ]
        barrier_services = [
            {
                "id": barrier_type.id,
                "title": barrier_type.title,
                "description": barrier_type.description,
                "category": "SERVICES",
            }
            for barrier_type in BarrierType.services.all()
        ]
        return barrier_goods + barrier_services

    def get_barrier_priorities(self):
        return [
            {
                "code": priority.code,
                "name": priority.name,
                "order": priority.order,
            }
            for priority in BarrierPriority.objects.all()
        ]

    def get_barrier_type_categories(self):
        return dict(
            (x, y) for x, y in BARRIER_TYPE_CATEGORIES if x != "GOODSANDSERVICES"
        )

    def get_reporting_stages(self):
        return dict((stage.code, stage.description) for stage in Stage.objects.all())

    def get_os_regions_and_countries(self):
        dh_countries = import_api_results("country")
        dh_os_regions = []
        for item in dh_countries:
            if item["overseas_region"] not in dh_os_regions:
                # there are few countries with no overseas region
                if item["overseas_region"] is not None:
                    dh_os_regions.append(item["overseas_region"])
        return dh_os_regions, dh_countries

    def get(self, request):
        status_types = dict((x, y) for x, y in PROBLEM_STATUS_TYPES)
        loss_range = dict((x, y) for x, y in ESTIMATED_LOSS_RANGE)
        stage_status = dict((x, y) for x, y in STAGE_STATUS)
        adv_boolean = dict((x, y) for x, y in ADV_BOOLEAN)
        govt_response = dict((x, y) for x, y in GOVT_RESPONSE)
        publish_response = dict((x, y) for x, y in PUBLISH_RESPONSE)
        report_status = dict((x, y) for x, y in REPORT_STATUS)
        support_type = dict((x, y) for x, y in SUPPORT_TYPE)
        barrier_status = dict((x, y) for x, y in BARRIER_STATUS)
        barrier_chance = dict((x, y) for x, y in BARRIER_CHANCE_OF_SUCCESS)
        barrier_inter_type = dict((x, y) for x, y in BARRIER_INTERACTION_TYPE)
        barrier_source = dict((x, y) for x, y in BARRIER_SOURCE)
        timeline_events = dict((x, y) for x, y in TIMELINE_EVENTS)

        dh_os_regions, dh_countries = self.get_os_regions_and_countries()
        dh_admin_areas = import_api_results("administrative-area")
        dh_sectors = import_api_results("sector")

        report_stages = self.get_reporting_stages()
        barrier_types = self.get_barrier_types()
        barrier_type_cat = self.get_barrier_type_categories()
        barrier_priorities = self.get_barrier_priorities()

        results = {
            "status_types": status_types,
            "loss_range": loss_range,
            "stage_status": stage_status,
            "adv_boolean": adv_boolean,
            "govt_response": govt_response,
            "publish_response": publish_response,
            "report_status": report_status,
            "report_stages": report_stages,
            "support_type": support_type,
            "barrier_types": barrier_types,
            "overseas_regions": dh_os_regions,
            "countries": dh_countries,
            "country_admin_areas": dh_admin_areas,
            "sectors": dh_sectors,
            "barrier_status": barrier_status,
            "barrier_type_categories": barrier_type_cat,
            "barrier_chance_of_success": barrier_chance,
            "barrier_interaction_types": barrier_inter_type,
            "barrier_source": barrier_source,
            "timeline_events": timeline_events,
            "barrier_priorities": barrier_priorities,
        }

        return Response(results, status=status.HTTP_200_OK)
