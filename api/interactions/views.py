from django.conf import settings
from django.shortcuts import get_object_or_404, render
from rest_framework import generics

from oauth2_provider.contrib.rest_framework.permissions import IsAuthenticatedOrTokenHasScope

from api.interactions.models import Document, Interaction
from api.interactions.serializers import DocumentSerializer, InteractionSerializer
from api.documents.views import BaseEntityDocumentModelViewSet

from api.core.viewsets import CoreViewSet
from api.barriers.models import (
    BarrierInstance,
)
from api.metadata.constants import (
    BARRIER_INTERACTION_TYPE,
)


class DocumentViewSet(BaseEntityDocumentModelViewSet):
    """Document ViewSet."""

    serializer_class = DocumentSerializer
    queryset = Document.objects.all()


class InteractionViewSet(CoreViewSet):
    def create(self, request, *args, **kwargs):
        """Create and one-time upload URL generation."""
        response = super().create(request, *args, **kwargs)
        entity_document = self.get_queryset().get(pk=response.data['id'])
        response.data['signed_upload_url'] = entity_document.document.get_signed_upload_url()

        return response


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
            created_by=self.request.user
        )


class BarrierIneractionDetail(generics.RetrieveUpdateAPIView):
    """
    Return details of a Barrier Interaction
    Allows the barrier interaction to be updated as well
    """
    lookup_field = "pk"
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer
