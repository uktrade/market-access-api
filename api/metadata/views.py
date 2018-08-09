import json
import os

import requests

from django.conf import settings
from django.shortcuts import render

from hawkrest import HawkAuthentication

from rest_framework import generics, status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from urlobject import URLObject

from api.metadata.constants import (
    ADV_BOOLEAN,
    BARRIER_STATUS,
    BARRIER_TYPE_CATEGORIES,
    BARRIER_CHANCE_OF_SUCCESS,
    BARRIER_INTERACTION_TYPE,
    CONTRIBUTOR_TYPE,
    ESTIMATED_LOSS_RANGE,
    GOVT_RESPONSE,
    PROBLEM_STATUS_TYPES,
    PUBLISH_RESPONSE,
    REPORT_STATUS,
    STAGE_STATUS,
    SUPPORT_TYPE,
)
from api.metadata.models import BarrierType
from api.reports.models import Stage


class MetadataView(generics.GenericAPIView):
    authentication_classes = (HawkAuthentication,)
    permission_classes = (IsAuthenticated,)
    MODELS = {"./country/": "countries"}

    def import_api_results(self, endpoint):
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

    def get(self, request):
        status_types = dict((x, y) for x, y in PROBLEM_STATUS_TYPES)
        loss_range = dict((x, y) for x, y in ESTIMATED_LOSS_RANGE)
        stage_status = dict((x, y) for x, y in STAGE_STATUS)
        adv_boolean = dict((x, y) for x, y in ADV_BOOLEAN)
        govt_response = dict((x, y) for x, y in GOVT_RESPONSE)
        publish_response = dict((x, y) for x, y in PUBLISH_RESPONSE)
        report_status = dict((x, y) for x, y in REPORT_STATUS)
        support_type = dict((x, y) for x, y in SUPPORT_TYPE)
        report_stages = dict(
            (stage.code, stage.description) for stage in Stage.objects.all()
        )
        barrier_types = [
            {
                "id": barrier_type.id,
                "title": barrier_type.title,
                "description": barrier_type.description,
                "category": barrier_type.category,
            }
            for barrier_type in BarrierType.objects.all()
        ]

        dh_countries = self.import_api_results("country")
        dh_sectors = self.import_api_results("sector")

        barrier_status = dict((x, y) for x, y in BARRIER_STATUS)
        barrier_type_cat = dict((x, y) for x, y in BARRIER_TYPE_CATEGORIES)
        barrier_chance = dict((x, y) for x, y in BARRIER_CHANCE_OF_SUCCESS)
        barrier_inter_type = dict((x, y) for x, y in BARRIER_INTERACTION_TYPE)

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
            "countries": dh_countries,
            "sectors": dh_sectors,
            "barrier_status": barrier_status,
            "barrier_type_categories": barrier_type_cat,
            "barrier_chance_of_success": barrier_chance,
            "barrier_interaction_types": barrier_inter_type,
        }

        return Response(results, status=status.HTTP_200_OK)
