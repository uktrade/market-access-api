import json

from django.conf import settings
from django.shortcuts import render

from hawkrest import HawkAuthentication

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .utils import (
    import_api_results,
    get_os_regions_and_countries,
    get_admin_areas,
    get_sectors,
    get_barrier_priorities,
    get_barrier_type_categories,
    get_barrier_types,
    get_reporting_stages
)

from api.metadata.constants import (
    ADV_BOOLEAN,
    BARRIER_PENDING,
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
from api.metadata.models import BarrierType, BarrierPriority
from api.barriers.models import Stage


class MetadataView(generics.GenericAPIView):
    if settings.HAWK_ENABLED:
        authentication_classes = (HawkAuthentication,)
        permission_classes = (IsAuthenticated,)
    else:
        authentication_classes = ()
        permission_classes = ()


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
        barrier_pending = dict((x, y) for x, y in BARRIER_PENDING)
        barrier_chance = dict((x, y) for x, y in BARRIER_CHANCE_OF_SUCCESS)
        barrier_inter_type = dict((x, y) for x, y in BARRIER_INTERACTION_TYPE)
        barrier_source = dict((x, y) for x, y in BARRIER_SOURCE)
        timeline_events = dict((x, y) for x, y in TIMELINE_EVENTS)

        dh_os_regions, dh_countries = get_os_regions_and_countries()
        dh_admin_areas = get_admin_areas()
        dh_sectors = get_sectors()

        report_stages = get_reporting_stages()
        barrier_types = get_barrier_types()
        barrier_type_cat = get_barrier_type_categories()
        barrier_priorities = get_barrier_priorities()

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
            "barrier_pending": barrier_pending,
            "barrier_type_categories": barrier_type_cat,
            "barrier_chance_of_success": barrier_chance,
            "barrier_interaction_types": barrier_inter_type,
            "barrier_source": barrier_source,
            "timeline_events": timeline_events,
            "barrier_priorities": barrier_priorities,
        }

        return Response(results, status=status.HTTP_200_OK)
