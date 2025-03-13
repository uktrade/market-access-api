import datetime

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import View
from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.assessment.models import EconomicAssessment
from api.barriers.models import Barrier, PublicBarrier
from api.collaboration.mixins import TeamMemberModelMixin
from api.documents.views import BaseEntityDocumentModelViewSet
from api.interactions.models import (
    Document,
    ExcludeFromNotification,
    Interaction,
    Mention,
    PublicBarrierNote,
)
from api.interactions.serializers import (
    DocumentSerializer,
    ExcludeFromNotificationSerializer,
    InteractionSerializer,
    MentionSerializer,
    PublicBarrierNoteSerializer,
)
from api.metadata.constants import BARRIER_INTERACTION_TYPE


class ExcludeNotification(View):
    def post(self, request):
        ExcludeFromNotification.objects.get_or_create(
            excluded_user=request.user,
            exclude_email=request.user.email,
            created_by=request.user,
            modified_by=request.user,
        )
        # if the record already exists don't duplicated it, else create the record
        return HttpResponse("success")

    def delete(self, request):
        user_qs = ExcludeFromNotification.objects.filter(excluded_user=request.user)
        if not user_qs.exists():
            # The user is not in the excluded list
            return HttpResponse("success")

        u = user_qs[0]
        u.delete()
        return HttpResponse("success")


class ExcludeFromNotificationsView(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        user_has_exclusion = (
            ExcludeFromNotification.objects.filter(excluded_user=request.user).count()
            > 0
        )

        if user_has_exclusion:
            data = ExcludeFromNotificationSerializer(
                data={"mention_notifications_enabled": False}
            )
            data.is_valid()
            return Response(data.validated_data)
        else:
            data = ExcludeFromNotificationSerializer(
                data={"mention_notifications_enabled": True}
            )
            data.is_valid()
            return Response(data.validated_data)

    def create(self, request):
        # if request.user.is_anonymous():
        #     raise Exception("User is anonymous")
        ExcludeFromNotification.objects.get_or_create(
            excluded_user=request.user,
            defaults={
                "exclude_email": request.user.email,
                "created_by": request.user,
                "modified_by": request.user,
            },
        )
        # if the record already exists don't duplicated it, else create the record
        return Response({"status": "success"})

    def destroy(self, request):
        user_qs = ExcludeFromNotification.objects.filter(excluded_user=request.user)
        if not user_qs.exists():
            # The user is not in the excluded list
            return Response({"status": "success"})

        u = user_qs[0]
        u.delete()
        return Response({"status": "success"})


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


class MentionsCounts(generics.GenericAPIView):
    schema = None

    def get(self, request, *args, **kwargs):
        qs = Mention.objects.filter(
            recipient=request.user,
            created_on__date__gte=(
                datetime.datetime.now() - datetime.timedelta(days=30)
            ),
        )
        return Response(
            {
                "read_by_recipient": qs.filter(read_by_recipient=True).count(),
                "total": qs.count(),
            }
        )


class MentionList(viewsets.ModelViewSet):
    serializer_class = MentionSerializer

    def get_queryset(self):
        return Mention.objects.filter(
            recipient=self.request.user,
            created_on__date__gte=(
                datetime.datetime.now() - datetime.timedelta(days=30)
            ),
        )

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

    def mark_all_as_read(self, request):
        self.get_queryset().filter(recipient=request.user).update(
            read_by_recipient=True
        )
        return Response({"status": "success"})

    def mark_all_as_unread(self, request):
        self.get_queryset().filter(recipient=request.user).update(
            read_by_recipient=False
        )
        return Response({"status": "success"})


class MentionDetail(
    TeamMemberModelMixin,
    generics.RetrieveAPIView,
):
    queryset = Mention.objects.all()
    serializer_class = MentionSerializer
