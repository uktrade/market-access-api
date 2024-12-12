from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from api.assessment.exceptions import BadRequest
from api.assessment.models import (
    EconomicAssessment,
    EconomicImpactAssessment,
    PreliminaryAssessment,
    ResolvabilityAssessment,
    StrategicAssessment,
)
from api.assessment.serializers import (
    EconomicAssessmentSerializer,
    EconomicImpactAssessmentSerializer,
    PreliminaryAssessmentSerializer,
    PreliminaryAssessmentUpdateSerializer,
    ResolvabilityAssessmentSerializer,
    StrategicAssessmentSerializer,
)
from api.barriers.models import Barrier


class BarrierPreliminaryAssessment(generics.GenericAPIView):
    serializer_class = PreliminaryAssessmentSerializer

    def post(self, request, barrier_id, *args, **kwargs):
        try:
            barrier = Barrier.objects.get(id=barrier_id)
        except Barrier.DoesNotExist:
            raise NotFound("Barrier")
        try:
            barrier.preliminary_assessment
            raise BadRequest("Preliminary Assessment Exists")
        except PreliminaryAssessment.DoesNotExist:
            pass

        data = {**request.data, **{"barrier_id": barrier_id}}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, barrier_id, *args, **kwargs):
        try:
            barrier = Barrier.objects.get(id=barrier_id)
        except Barrier.DoesNotExist:
            raise NotFound("Barrier")

        try:
            serializer = self.get_serializer(barrier.preliminary_assessment)
        except PreliminaryAssessment.DoesNotExist:
            raise NotFound("Preliminary Assessment")

        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, barrier_id, *args, **kwargs):
        try:
            barrier = Barrier.objects.get(id=barrier_id)
            if not barrier.preliminary_assessment:
                raise NotFound("Preliminary assessment not found")
        except (Barrier.DoesNotExist, PreliminaryAssessment.DoesNotExist):
            raise NotFound("Barrier not found")

        request = PreliminaryAssessmentUpdateSerializer(request.data)

        serializer = self.get_serializer(
            barrier.preliminary_assessment, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


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
