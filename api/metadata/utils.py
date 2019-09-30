import json
import os
import requests
import logging

from urlobject import URLObject

from django.conf import settings

from api.metadata.constants import (
    BARRIER_TYPE_CATEGORIES
)
from api.metadata.models import BarrierType, BarrierPriority
from api.barriers.models import Stage

from mohawk import Sender

creds = {
        'id' : settings.HAWK_ID,
        'key' : settings.HAWK_CREDENTIALS[settings.HAWK_ID]["key"],
        'algorithm' : 'sha256'}


def import_api_results(endpoint):
    # Avoid calling DH
    fake_it = settings.FAKE_METADATA
    if fake_it:
        file_path = os.path.join(settings.BASE_DIR, f"static/{endpoint}.json")
        return json.loads(open(file_path).read())

    base_url = URLObject(settings.DH_METADATA_URL)
    meta_url = base_url.relative(f"./{endpoint}")

    sender = Sender(creds, 
        meta_url, 
        'GET', 
        content=None, 
        content_type=None, 
        always_hash_content=False,
    )
        
    response = requests.get(meta_url, verify=not settings.DEBUG, 
        headers = {
            'Authorization' : sender.request_header
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

def get_barrier_types():
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
