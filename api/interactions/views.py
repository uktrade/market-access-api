from api.assessment.models import EconomicAssessment
from api.barriers.models import Barrier, PublicBarrier
from api.collaboration.mixins import TeamMemberModelMixin
from api.documents.views import BaseEntityDocumentModelViewSet
from api.interactions.models import (
    Document,
    ExcludeFromNotifcation,
    Interaction,
    Mention,
    PublicBarrierNote,
)
from api.interactions.serializers import (
    DocumentSerializer,
    InteractionSerializer,
    MentionSerializer,
    PublicBarrierNoteSerializer,
)
from api.metadata.constants import BARRIER_INTERACTION_TYPE

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.generic.base import View
from django.http import HttpResponse

from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class ExcludeNotifcation(View):
    def post(self, request):
        ExcludeFromNotifcation.objects.get_or_create(
            excluded_user=request.user,
            exclude_email=request.user.email,
            created_by=request.user,
            modified_by=request.user,
        )
        # if the record already exists don't duplicated it, else create the record
        return HttpResponse("success")

    def delete(self, request):
        user_qs = ExcludeFromNotifcation.objects.filter(excluded_user=request.user)
        if not user_qs.exists():
            # The user is not in the excluded list
            return HttpResponse("success")

        u = user_qs[0]
        u.delete()
        return HttpResponse("success")


class DocumentViewSet(BaseEntityDocumentModelViewSet):
    """Document ViewSet."""

    serializer_class = DocumentSerializer
    queryset = Document.objects.all()

    @staticmethod
    def _is_document_attached(document):
        if (
            Interaction.objects.filter(documents=document.id).count() > 0
            or EconomicAssessment.objects.filter(documents=document.id).count() > 0
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


class BarrierInteractionList(TeamMemberModelMixin, generics.ListCreateAPIView):
    """
    Handling Barrier interactions, such as notes
    """

    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk"))

    def perform_create(self, serializer):
        barrier = get_object_or_404(Barrier, pk=self.kwargs.get("pk"))
        kind = self.request.data.get("kind", BARRIER_INTERACTION_TYPE["COMMENT"])
        docs_in_req = self.request.data.get("documents", None)
        documents = []
        if docs_in_req:
            documents = [get_object_or_404(Document, pk=id) for id in docs_in_req]
        serializer.save(
            barrier=barrier,
            kind=kind,
            documents=documents,
            created_by=self.request.user,
        )
        # Update Team members
        self.update_contributors(barrier)


class BarrierInteractionDetail(
    TeamMemberModelMixin, generics.RetrieveUpdateDestroyAPIView
):
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

    @transaction.atomic()
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
        # Update Team members
        self.update_contributors(interaction.barrier)

    def perform_destroy(self, instance):
        instance.archive(self.request.user)


class PublicBarrierNoteList(TeamMemberModelMixin, generics.ListCreateAPIView):
    serializer_class = PublicBarrierNoteSerializer

    def get_queryset(self):
        return PublicBarrierNote.objects.filter(
            public_barrier__barrier_id=self.kwargs.get("barrier_id"),
            archived=False,
        )

    def perform_create(self, serializer):
        barrier_id = self.kwargs.get("barrier_id")
        public_barrier = get_object_or_404(PublicBarrier, barrier_id=barrier_id)
        serializer.save(public_barrier=public_barrier, created_by=self.request.user)
        self.update_contributors(public_barrier.barrier)


class PublicBarrierNoteDetail(
    TeamMemberModelMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    queryset = PublicBarrierNote.objects.all()
    serializer_class = PublicBarrierNoteSerializer

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)
        note = self.get_object()
        self.update_contributors(note.public_barrier.barrier)

    def perform_destroy(self, instance):
        instance.archive(self.request.user)


class MentionList(viewsets.ModelViewSet):
    serializer_class = MentionSerializer

    def get_queryset(self):
        return Mention.objects.filter(recipient=self.request.user)

    def mark_as_read(self, request, pk):
        mention = self.get_queryset().get(pk=pk)
        mention.read_by_recipient = True
        mention.save()
        serializer = MentionSerializer(mention)
        return Response(serializer.data)

    def mark_as_unread(self, request, pk):
        mention = self.get_queryset().get(pk=pk)
        mention.read_by_recipient = False
        mention.save()
        serializer = MentionSerializer(mention)
        return Response(serializer.data)
