import json
import os
import requests
from urlobject import URLObject

from django.conf import settings

from api.metadata.constants import (
    BARRIER_TYPE_CATEGORIES
)
from api.metadata.models import Category, BarrierPriority
from api.barriers.models import Stage

from mohawk import Sender


def import_api_results(endpoint):
    # Avoid calling DH
    fake_it = settings.FAKE_METADATA
    if fake_it:
        file_path = os.path.join(settings.BASE_DIR, f"static/{endpoint}.json")
        return json.loads(open(file_path).read())

    base_url = URLObject(settings.DH_METADATA_URL)

    # v4 endpoints do not have trailing forward slash
    meta_url = base_url.relative(f"./{endpoint}")

    credentials = settings.HAWK_CREDENTIALS[settings.DATAHUB_HAWK_ID]

    sender = Sender(credentials,
                    meta_url,
                    'GET',
                    content=None,
                    content_type=None,
                    always_hash_content=False,
                    )

    response = requests.get(meta_url, verify=not settings.DEBUG,
                            headers={
                                'Authorization': sender.request_header
                            })

    if response.ok:
        return response.json()

    return None

def get_os_regions_and_countries():
    dh_countries = import_api_results("country")
    dh_os_regions = []
    for item in dh_countries:
        if item["overseas_region"] not in dh_os_regions:
            # there are few countries with no overseas region
            if item["overseas_region"] is not None:
                dh_os_regions.append(item["overseas_region"])
    return dh_os_regions, dh_countries

def get_countries():
    dh_regions, dh_countries = get_os_regions_and_countries()
    return dh_countries

def get_admin_areas():
    return import_api_results("administrative-area")

def get_sectors():
    return import_api_results("sector")

def get_categories():
    barrier_goods = [
        {
            "id": category.id,
            "title": category.title,
            "description": category.description,
            "category": "GOODS",
        }
        for category in Category.goods.all()
    ]
    barrier_services = [
        {
            "id": category.id,
            "title": category.title,
            "description": category.description,
            "category": "SERVICES",
        }
        for category in Category.services.all()
    ]
    return barrier_goods + barrier_services

def get_barrier_priorities():
    return [
        {"code": priority.code, "name": priority.name, "order": priority.order}
        for priority in BarrierPriority.objects.all()
    ]

def get_barrier_type_categories():
    return dict(
        (x, y) for x, y in BARRIER_TYPE_CATEGORIES if x != "GOODSANDSERVICES"
    )

def get_reporting_stages():
    return dict((stage.code, stage.description) for stage in Stage.objects.order_by('id'))
