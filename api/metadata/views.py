from hawkrest import HawkAuthentication
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.metadata.constants import (
    BARRIER_CHANCE_OF_SUCCESS,
    BARRIER_INTERACTION_TYPE,
    BARRIER_PENDING,
    BARRIER_SOURCE,
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
    TOP_PRIORITY_BARRIER_STATUS,
    TRADE_CATEGORIES,
    TRADE_DIRECTION_CHOICES,
    TRADING_BLOCS,
    BarrierStatus,
)
from api.metadata.utils import (
    get_admin_areas,
    get_barrier_priorities,
    get_barrier_search_ordering_choices,
    get_barrier_tags,
    get_barrier_type_categories,
    get_government_organisations,
    get_os_regions_and_countries,
    get_policy_teams,
    get_reporting_stages,
    get_sectors,
    get_wto_committee_groups,
)


class MetadataView(generics.GenericAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        barrier_terms = dict(BARRIER_TERMS)
        loss_range = dict(ESTIMATED_LOSS_RANGE)
        stage_status = dict(STAGE_STATUS)
        govt_response = dict(GOVT_RESPONSE)
        publish_response = dict(PUBLISH_RESPONSE)
        report_status = dict(REPORT_STATUS)
        support_type = dict(SUPPORT_TYPE)
        # skip OPEN_PENDING as it's not used in the frontend
        barrier_status = dict(
            [
                choice
                for choice in BarrierStatus.choices
                if choice[0] != BarrierStatus.OPEN_PENDING
            ]
        )
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
        top_priority_barrier_status = dict(TOP_PRIORITY_BARRIER_STATUS)

        dh_os_regions, dh_countries = get_os_regions_and_countries()
        dh_admin_areas = get_admin_areas()
        dh_sectors = get_sectors()

        report_stages = get_reporting_stages()
        policy_teams = get_policy_teams()
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
            "policy_teams": policy_teams,
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
            "government_organisations": government_organisations,
            "resolvability_assessment_effort": assessment_effort_to_resolve,
            "resolvability_assessment_time": assessment_time_to_resolve,
            "strategic_assessment_scale": strategic_assessment_scale,
            "top_priority_status": top_priority_barrier_status,
            "trade_categories": trade_categories,
            "trade_direction": trade_direction,
            "trading_blocs": TRADING_BLOCS.values(),
            "wto_committee_groups": wto_committee_groups,
            "search_ordering_choices": get_barrier_search_ordering_choices(),
        }

        return Response(results, status=status.HTTP_200_OK)
