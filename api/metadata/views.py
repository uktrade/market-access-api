from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.metadata.constants import STATUS_TYPES


@permission_classes([IsAuthenticated])
class MetadataView(generics.GenericAPIView):

    def get(self, request):
        status_types = dict((x, y) for x, y in STATUS_TYPES)
        results = {
            'status_types': status_types,
        }

        return Response(results, status=status.HTTP_200_OK)
