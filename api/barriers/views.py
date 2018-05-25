from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from api.barriers.models import Barrier
from api.barriers.serializers import BarrierListSerializer, BarrierDetailSerializer


@permission_classes([IsAuthenticated])
class BarrierList(generics.ListCreateAPIView):
    queryset = Barrier.objects.all()
    serializer_class = BarrierListSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


@permission_classes([IsAuthenticated])
class BarrierDetail(generics.RetrieveUpdateAPIView):

    lookup_field = 'pk'
    queryset = Barrier.objects.all()
    serializer_class = BarrierDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
