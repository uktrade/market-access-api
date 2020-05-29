from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError

from api.assessment.models import Assessment
from api.interactions.models import Document, Interaction
from api.interactions.serializers import DocumentSerializer, InteractionSerializer
from api.documents.views import BaseEntityDocumentModelViewSet

from api.barriers.models import BarrierInstance
from api.metadata.constants import BARRIER_INTERACTION_TYPE


class DocumentViewSet(BaseEntityDocumentModelViewSet):
    """Document ViewSet."""

    serializer_class = DocumentSerializer
    queryset = Document.objects.all()

    @staticmethod
    def _is_document_attached(document):
        if (
            Interaction.objects.filter(documents=document.id).count() > 0
            or Assessment.objects.filter(documents=document.id).count() > 0
        ):
            return True
        return False

    def perform_destroy(self, instance):
        """
        Customise document delete,
        if it is actively attached to a note, raise validation error
        if it was detached already, skip it
        only if was never attached to any note, delete it from S3
        """
        doc = Document.objects.get(id=str(instance.pk))
        if self._is_document_attached(doc):
            raise ValidationError()
        if not doc.detached:
            return super().perform_destroy(instance)


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


class BarrierIneractionDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Return details of a Barrier Interaction
    Allows the barrier interaction to be updated
    and deleted (archive)
    """

    lookup_field = "pk"
    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        """
        This needs to attach new set of documents
        And detach the ones that not present in the request, but were previously attached
        """
        interaction = self.get_object()
        if "documents" in self.request.data:
            docs_in_req = self.request.data.get("documents", None)
            docs_to_add = []
            if docs_in_req:
                docs_to_add = [get_object_or_404(Document, pk=id) for id in docs_in_req]
            docs_to_detach = list(set(interaction.documents.all()) - set(docs_to_add))
            serializer.save(documents=docs_to_add, modified_by=self.request.user)
            interaction = self.get_object()
            for doc in docs_to_detach:
                interaction.documents.remove(doc)
                doc.detached = True
                doc.save()
        else:
            serializer.save(modified_by=self.request.user)
        interaction.barrier.save()

    def perform_destroy(self, instance):
        instance.archive(self.request.user)
