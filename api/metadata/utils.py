import json
import os
from functools import lru_cache
from typing import Dict, List

import requests
import sentry_sdk
from django.conf import settings
from django.core.cache import cache
from mohawk import Sender
from rest_framework.exceptions import APIException
from urlobject import URLObject

from api.wto import models as wto_models

from .constants import (
    BARRIER_SEARCH_ORDERING_CHOICES,
    BARRIER_TYPE_CATEGORIES,
    GOVERNMENT_ORGANISATION_TYPES,
    TRADING_BLOCS,
)
from .models import BarrierPriority, BarrierTag, Category, Organisation, PolicyTeam


def import_api_results(endpoint):
    # Avoid calling DH
    fake_it = settings.FAKE_METADATA
    if fake_it:
        # TODO: fake all metadata, not just a part of it
        #       currently only a few countries are made available
        file_path = os.path.join(settings.BASE_DIR, f"static/{endpoint}.json")
        return json.loads(open(file_path).read())

    base_url = URLObject(settings.DH_METADATA_URL)

    # v4 endpoints do not have trailing forward slash
    meta_url = base_url.relative(f"./{endpoint}")

    credentials = settings.HAWK_CREDENTIALS[settings.DATAHUB_HAWK_ID]

    sender = Sender(
        credentials,
        meta_url,
        "GET",
        content=None,
        content_type=None,
        always_hash_content=False,
    )

    response = requests.get(
        meta_url,
        verify=not settings.DEBUG,
        headers={"Authorization": sender.request_header},
    )

    if not response.ok:
        with sentry_sdk.push_scope() as scope:
            scope.set_extra("datahub_response", response)
            raise APIException(f"Error fetching metadata from DataHub for {endpoint}")

    return response.json()


def get_os_regions_and_countries():
    dh_countries = import_api_results("country")
    dh_os_regions = []
    for item in dh_countries:
        if item["overseas_region"] not in dh_os_regions:
            # there are few countries with no overseas region
            if item["overseas_region"] is not None:
                dh_os_regions.append(item["overseas_region"])

    # Add custom overseas region; Wider Europe
    dh_os_regions.append({"name": "Wider Europe", "id": "wider_europe"})

    return dh_os_regions, dh_countries


def get_country(country_id):
    country_lookup = cache.get("dh_country_lookup")
    if not country_lookup:
        country_lookup = {country["id"]: country for country in get_countries()}
        cache.set("dh_country_lookup", country_lookup, 7200)
    country = country_lookup.get(country_id)
    if country:
        country["trading_bloc"] = get_trading_bloc_by_country_id(country["id"])
    return country


def get_countries():
    dh_regions, dh_countries = get_os_regions_and_countries()
    return dh_countries


def get_country_ids_by_overseas_region(region_id):
    countries = get_countries()
    return [
        country["id"]
        for country in countries
        if country.get("overseas_region")
        and region_id == country.get("overseas_region").get("id")
    ]


def get_admin_area(admin_area_id):
    admin_area_lookup = cache.get("dh_admin_area_lookup")
    if not admin_area_lookup:
        admin_area_lookup = {
            admin_area["id"]: admin_area for admin_area in get_admin_areas()
        }
        cache.set("dh_admin_area_lookup", admin_area_lookup, 7200)
    return admin_area_lookup.get(str(admin_area_id))


def get_admin_areas():
    return import_api_results("administrative-area")


def get_overseas_region(overseas_region_id):
    overseas_region_lookup = cache.get("dh_overseas_region_lookup")
    if not overseas_region_lookup:
        dh_countries = import_api_results("country")
        overseas_region_lookup = {}
        for country in dh_countries:
            if country.get("overseas_region"):
                overseas_region = country["overseas_region"]
                overseas_region_lookup[overseas_region["id"]] = overseas_region

        cache.set("dh_overseas_region_lookup", overseas_region_lookup, 7200)
    return overseas_region_lookup.get(str(overseas_region_id))


def get_sector(sector_id):
    sector_lookup = cache.get("dh_sector_lookup")
    if not sector_lookup:
        sector_lookup = {sector["id"]: sector for sector in get_sectors()}
        cache.set("dh_sector_lookup", sector_lookup, 7200)
    return sector_lookup.get(str(sector_id))


def get_sectors():
    return import_api_results("sector")


def get_policy_teams() -> List[Dict]:
    from api.metadata.serializers import PolicyTeamSerializer

    return PolicyTeamSerializer(PolicyTeam.objects.all(), many=True).data


def get_barrier_tags():
    return list(
        BarrierTag.objects.values(
            "id", "title", "description", "show_at_reporting", "order"
        )
    )


@lru_cache
def get_barrier_tag_from_title(title: str):
    tags = get_barrier_tags()
    for tag in tags:
        if tag["title"] == title:
            return tag


def get_barrier_priorities():
    return [
        {"code": priority.code, "name": priority.name, "order": priority.order}
        for priority in BarrierPriority.objects.all()
    ]


def get_barrier_type_categories():
    return dict((x, y) for x, y in BARRIER_TYPE_CATEGORIES if x != "GOODSANDSERVICES")


def get_reporting_stages():
    from api.barriers.models import Stage

    return dict(
        (stage.code, stage.description) for stage in Stage.objects.order_by("id")
    )


def get_trading_bloc(code):
    trading_bloc = TRADING_BLOCS.get(code)
    if trading_bloc:
        return {
            "code": trading_bloc["code"],
            "name": trading_bloc["name"],
            "short_name": trading_bloc["short_name"],
            "overseas_regions": get_trading_bloc_overseas_regions(trading_bloc["code"]),
        }


def get_trading_bloc_by_country_id(country_id):
    for trading_bloc in TRADING_BLOCS.values():
        if country_id in trading_bloc["country_ids"]:
            return {
                "code": trading_bloc["code"],
                "name": trading_bloc["name"],
                "short_name": trading_bloc["short_name"],
                "overseas_regions": get_trading_bloc_overseas_regions(
                    trading_bloc["code"]
                ),
            }


def get_trading_bloc_country_ids(trading_bloc_code):
    return TRADING_BLOCS.get(trading_bloc_code, {}).get("country_ids", [])


def get_trading_bloc_overseas_region_ids(trading_bloc_code):
    return TRADING_BLOCS.get(trading_bloc_code, {}).get("overseas_regions", [])


def get_trading_bloc_overseas_regions(trading_bloc_code):
    overseas_region_ids = get_trading_bloc_overseas_region_ids(trading_bloc_code)
    return [get_overseas_region(region_id) for region_id in overseas_region_ids]


def get_wto_committee_groups():
    committee_groups = []
    for group in wto_models.WTOCommitteeGroup.objects.prefetch_related("committees"):
        committee_groups.append(
            {
                "id": str(group.id),
                "name": group.name,
                "wto_committees": [
                    {
                        "id": str(committee.id),
                        "name": committee.name,
                    }
                    for committee in group.committees.all()
                ],
            }
        )
    return committee_groups


def get_location_text(
    country_id, trading_bloc=None, caused_by_trading_bloc=None, admin_area_ids=()
):
    if not country_id:
        if trading_bloc:
            return TRADING_BLOCS.get(trading_bloc, {}).get("name")
        return None

    country = get_country(str(country_id))
    if not country:
        return None
    country_name = country["name"]

    if caused_by_trading_bloc and country.get("trading_bloc"):
        trading_bloc = country.get("trading_bloc", {}).get("name", "")
        return f"{country_name} ({trading_bloc})"

    if admin_area_ids:

        def admin_area_name(admin_area_id):
            admin_area = get_admin_area(admin_area_id) or {}
            return admin_area.get("name", "")

        admin_areas_string = ", ".join(admin_area_name(_id) for _id in admin_area_ids)
        return f"{admin_areas_string} ({country_name})"

    return country_name


def get_government_organisations():
    return list(
        Organisation.objects.filter(
            organisation_type__in=GOVERNMENT_ORGANISATION_TYPES
        ).values("id", "name", "organisation_type")
    )


def get_barrier_search_ordering_choices():
    return [
        (ordering, config["label"])
        for ordering, config in BARRIER_SEARCH_ORDERING_CHOICES.items()
    ]
