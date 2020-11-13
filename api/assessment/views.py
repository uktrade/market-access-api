from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.response import Response

from api.assessment.models import EconomicAssessment, ResolvabilityAssessment, StrategicAssessment
from api.assessment.serializers import (
    EconomicAssessmentSerializer,
    ResolvabilityAssessmentSerializer,
    StrategicAssessmentSerializer,
)

from api.barriers.models import Barrier
from api.core.utils import cleansed_username
from api.interactions.models import Document


class EconomicAssessmentList(generics.CreateAPIView):
    queryset = EconomicAssessment.objects.all()
    serializer_class = EconomicAssessmentSerializer


class EconomicAssessmentDetail(generics.RetrieveUpdateAPIView):
    queryset = EconomicAssessment.objects.all()
    serializer_class = EconomicAssessmentSerializer


class ResolvabilityAssessmentList(generics.CreateAPIView):
    queryset = ResolvabilityAssessment.objects.all()
    serializer_class = ResolvabilityAssessmentSerializer


class ResolvabilityAssessmentDetail(generics.RetrieveUpdateAPIView):
    queryset = ResolvabilityAssessment.objects.all()
    serializer_class = ResolvabilityAssessmentSerializer


class StrategicAssessmentList(generics.CreateAPIView):
    queryset = StrategicAssessment.objects.all()
    serializer_class = StrategicAssessmentSerializer


class StrategicAssessmentDetail(generics.RetrieveUpdateAPIView):
    queryset = StrategicAssessment.objects.all()
    serializer_class = StrategicAssessmentSerializer
