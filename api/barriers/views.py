from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from api.core.auth import IsMAServer, IsMAUser
from api.barriers.models import Barrier
from api.barriers.serializers import BarrierListSerializer, BarrierDetailSerializer

MI_PERMISSION_CLASSES = (IsMAServer, IsMAUser)


class BarrierList(generics.ListCreateAPIView):
    permission_classes = MI_PERMISSION_CLASSES
    queryset = Barrier.objects.all()
    serializer_class = BarrierListSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class BarrierDetail(generics.RetrieveUpdateAPIView):
    permission_classes = MI_PERMISSION_CLASSES

    lookup_field = 'pk'
    queryset = Barrier.objects.all()
    serializer_class = BarrierDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
