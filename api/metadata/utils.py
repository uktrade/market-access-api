import json
import os
import requests
from urlobject import URLObject

from django.conf import settings


def import_api_results(endpoint):
    # Avoid calling DH
    fake_it = settings.FAKE_METADATA
    if fake_it:
        file_path = os.path.join(
            settings.BASE_DIR, f"static/{endpoint}.json"
        )
        return json.loads(open(file_path).read())
    base_url = URLObject(settings.DH_METADATA_URL)
    meta_url = base_url.relative(f"./{endpoint}/")

    response = requests.get(meta_url, verify=not settings.DEBUG)
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
