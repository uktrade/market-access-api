from rest_framework import generics

from api.assessment.models import (EconomicAssessment,
                                   EconomicImpactAssessment,
                                   ResolvabilityAssessment,
                                   StrategicAssessment)
from api.assessment.serializers import (EconomicAssessmentSerializer,
                                        EconomicImpactAssessmentSerializer,
                                        ResolvabilityAssessmentSerializer,
                                        StrategicAssessmentSerializer)


class EconomicAssessmentList(generics.CreateAPIView):
    queryset = EconomicAssessment.objects.all()
    serializer_class = EconomicAssessmentSerializer


class EconomicAssessmentDetail(generics.RetrieveUpdateAPIView):
    queryset = EconomicAssessment.objects.all()
    serializer_class = EconomicAssessmentSerializer


class EconomicImpactAssessmentList(generics.CreateAPIView):
    queryset = EconomicImpactAssessment.objects.all()
    serializer_class = EconomicImpactAssessmentSerializer


class EconomicImpactAssessmentDetail(generics.RetrieveUpdateAPIView):
    queryset = EconomicImpactAssessment.objects.all()
    serializer_class = EconomicImpactAssessmentSerializer


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
