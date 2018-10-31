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
            settings.BASE_DIR, f"api/metadata/static/{endpoint}.json"
        )
        return json.loads(open(file_path).read())
    base_url = URLObject(settings.DH_METADATA_URL)
    meta_url = base_url.relative(f"./{endpoint}/")

    response = requests.get(meta_url, verify=not settings.DEBUG)
    if response.ok:
        return response.json()

    return None
