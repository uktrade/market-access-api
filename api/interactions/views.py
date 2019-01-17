from django.conf import settings
from django.shortcuts import get_object_or_404, render
from rest_framework import generics
from rest_framework.response import Response

from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)

from api.interactions.models import Document, Interaction
from api.interactions.serializers import DocumentSerializer, InteractionSerializer
from api.documents.views import BaseEntityDocumentModelViewSet

from api.core.viewsets import CoreViewSet
from api.barriers.models import BarrierInstance
from api.metadata.constants import BARRIER_INTERACTION_TYPE


class DocumentViewSet(BaseEntityDocumentModelViewSet):
    """Document ViewSet."""

    serializer_class = DocumentSerializer
    queryset = Document.objects.all()


class BarrierInteractionList(generics.ListCreateAPIView):
    """
    Handling Barrier interactions, such as notes
    """

    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk"))

    def perform_create(self, serializer):
        barrier_obj = get_object_or_404(BarrierInstance, pk=self.kwargs.get("pk"))
        kind = self.request.data.get("kind", BARRIER_INTERACTION_TYPE["COMMENT"])
        docs_in_req = self.request.data.get("documents", None)
        documents = []
        if docs_in_req:
            documents = [get_object_or_404(Document, pk=id) for id in docs_in_req]
        serializer.save(
            barrier=barrier_obj,
            kind=kind,
            documents=documents,
            created_by=self.request.user,
        )
        barrier_obj.save()


class BarrierIneractionDetail(generics.RetrieveUpdateAPIView):
    """
    Return details of a Barrier Interaction
    Allows the barrier interaction to be updated as well
    """

    lookup_field = "pk"
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        interaction = self.get_object()
        if "documents" in self.request.data:
            docs_in_req = self.request.data.get("documents", [])
            documents = [get_object_or_404(Document, pk=id) for id in docs_in_req]
            serializer.save(documents=documents, modified_by=self.request.user)
        else:
            serializer.save(modified_by=self.request.user)
        interaction.barrier.save()
