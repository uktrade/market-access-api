from django.conf import settings

from hawkrest import HawkAuthentication

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .constants import (
    BARRIER_PENDING,
    BARRIER_SOURCE,
    BarrierStatus,
    BARRIER_CHANCE_OF_SUCCESS,
    BARRIER_INTERACTION_TYPE,
    BARRIER_TERMS,
    ECONOMIC_ASSESSMENT_IMPACT,
    ECONOMIC_ASSESSMENT_RATING,
    ESTIMATED_LOSS_RANGE,
    GOVT_RESPONSE,
    PUBLISH_RESPONSE,
    REPORT_STATUS,
    RESOLVABILITY_ASSESSMENT_EFFORT,
    RESOLVABILITY_ASSESSMENT_TIME,
    STAGE_STATUS,
    STRATEGIC_ASSESSMENT_SCALE,
    SUPPORT_TYPE,
    TRADE_CATEGORIES,
    TRADE_DIRECTION_CHOICES,
    TRADING_BLOCS,
)
from .utils import (
    get_admin_areas,
    get_barrier_priorities,
    get_barrier_tags,
    get_barrier_type_categories,
    get_categories,
    get_os_regions_and_countries,
    get_reporting_stages,
    get_sectors,
    get_wto_committee_groups, get_government_organisations,
)


class MetadataView(generics.GenericAPIView):
    if settings.HAWK_ENABLED:
        authentication_classes = (HawkAuthentication,)
        permission_classes = (IsAuthenticated,)
    else:
        authentication_classes = ()
        permission_classes = ()

    def get(self, request):
        barrier_terms = dict(BARRIER_TERMS)
        loss_range = dict(ESTIMATED_LOSS_RANGE)
        stage_status = dict(STAGE_STATUS)
        govt_response = dict(GOVT_RESPONSE)
        publish_response = dict(PUBLISH_RESPONSE)
        report_status = dict(REPORT_STATUS)
        support_type = dict(SUPPORT_TYPE)
        barrier_status = dict(BarrierStatus.choices)
        barrier_pending = dict(BARRIER_PENDING)
        barrier_chance = dict(BARRIER_CHANCE_OF_SUCCESS)
        barrier_inter_type = dict(BARRIER_INTERACTION_TYPE)
        barrier_source = dict(BARRIER_SOURCE)
        trade_categories = dict(TRADE_CATEGORIES)
        economic_assessment_impact = dict(ECONOMIC_ASSESSMENT_IMPACT)
        economic_assessment_rating = dict(ECONOMIC_ASSESSMENT_RATING)
        assessment_effort_to_resolve = dict(RESOLVABILITY_ASSESSMENT_EFFORT)
        assessment_time_to_resolve = dict(RESOLVABILITY_ASSESSMENT_TIME)
        strategic_assessment_scale = dict(STRATEGIC_ASSESSMENT_SCALE)

        dh_os_regions, dh_countries = get_os_regions_and_countries()
        dh_admin_areas = get_admin_areas()
        dh_sectors = get_sectors()

        report_stages = get_reporting_stages()
        categories = get_categories()
        barrier_type_cat = get_barrier_type_categories()
        barrier_priorities = get_barrier_priorities()
        barrier_tags = get_barrier_tags()
        trade_direction = dict((str(x), y) for x, y in TRADE_DIRECTION_CHOICES)
        wto_committee_groups = get_wto_committee_groups()

        government_organisations = get_government_organisations()

        results = {
            "barrier_terms": barrier_terms,
            "loss_range": loss_range,
            "stage_status": stage_status,
            "govt_response": govt_response,
            "publish_response": publish_response,
            "report_status": report_status,
            "report_stages": report_stages,
            "support_type": support_type,
            "barrier_types": categories,
            "categories": categories,
            "overseas_regions": dh_os_regions,
            "countries": dh_countries,
            "admin_areas": dh_admin_areas,
            "sectors": dh_sectors,
            "barrier_status": barrier_status,
            "barrier_pending": barrier_pending,
            "barrier_tags": barrier_tags,
            "barrier_type_categories": barrier_type_cat,
            "barrier_chance_of_success": barrier_chance,
            "barrier_interaction_types": barrier_inter_type,
            "barrier_source": barrier_source,
            "barrier_priorities": barrier_priorities,
            "economic_assessment_impact": economic_assessment_impact,
            "economic_assessment_rating": economic_assessment_rating,
            "resolvability_assessment_effort": assessment_effort_to_resolve,
            "resolvability_assessment_time": assessment_time_to_resolve,
            "strategic_assessment_scale": strategic_assessment_scale,
            "trade_categories": trade_categories,
            "trade_direction": trade_direction,
            "trading_blocs": TRADING_BLOCS.values(),
            "wto_committee_groups": wto_committee_groups,
            "government_organisations": government_organisations,
        }

        return Response(results, status=status.HTTP_200_OK)
