import requests

from django.conf import settings
from django.shortcuts import render

from rest_framework import generics, status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from urlobject import URLObject

from api.reports.models import Stage
from api.metadata.constants import (
    PROBLEM_STATUS_TYPES,
    ESTIMATED_LOSS_RANGE,
    STAGE_STATUS,
    ADV_BOOLEAN,
    GOVT_RESPONSE,
    PUBLISH_RESPONSE,
    REPORT_STATUS
)


class MetadataView(generics.GenericAPIView):
    MODELS = {
        './country/': 'countries',
    }

    def import_api_results(self, endpoint):
        base_url = URLObject(settings.DH_METADATA_URL)
        meta_url = base_url.relative(endpoint)

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
        report_stages = dict((stage.code, stage.description)
                             for stage in Stage.objects.all())

        dh_countries = self.import_api_results('./country/')

        results = {
            'status_types': status_types,
            'loss_range': loss_range,
            'stage_status': stage_status,
            'adv_boolean': adv_boolean,
            'govt_response': govt_response,
            'publish_response': publish_response,
            'report_status': report_status,
            'report_stages': report_stages,
            'countries': dh_countries
        }

        return Response(results, status=status.HTTP_200_OK)
