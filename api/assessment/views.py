from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from api.assessment.models import Assessment
from api.assessment.serializers import AssessmentSerializer
from api.documents.views import BaseEntityDocumentModelViewSet

from api.barriers.models import BarrierInstance
from api.interactions.models import Document
from api.metadata.constants import ASSESMENT_IMPACT


class BarrierAssessmentDetail(generics.CreateAPIView,
                        generics.RetrieveUpdateAPIView):
    """
    Return details of a Barrier Assessment
    Allows the barrier assessment to be created and updated
    """

    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer

    def get_queryset(self):
        barrier_obj = get_object_or_404(BarrierInstance, pk=self.kwargs.get("pk"))
        return self.queryset.filter(barrier=barrier_obj)

    def get_object(self):
        barrier_obj = get_object_or_404(BarrierInstance, pk=self.kwargs.get("pk"))
        # May raise a permission denied
        self.check_object_permissions(self.request, barrier_obj)

        if hasattr(barrier_obj, 'assessment'):
            return barrier_obj.assessment

        raise Http404('No %s matches the given query.' % self.queryset.model._meta.object_name)

    def perform_create(self, serializer):
        barrier_obj = get_object_or_404(BarrierInstance, pk=self.kwargs.get("pk"))

        if hasattr(barrier_obj, 'assessment'):
            raise serializers.ValidationError("Assessment already exists")

        impact = self.request.data.get("impact", None)
        explanation = self.request.data.get("explanation", None)
        docs_in_req = self.request.data.get("documents", None)
        documents = []
        if docs_in_req:
            documents = [get_object_or_404(Document, pk=id) for id in docs_in_req]
        serializer.save(
            barrier=barrier_obj,
            impact=impact,
            explanation=explanation,
            documents=documents,
            created_by=self.request.user,
        )

    def patch(self, request, pk):
        assessment = self.get_object()
        serializer = AssessmentSerializer(
            assessment,
            data=request.data,
            partial=True
        )
        if "documents" in self.request.data:
            docs_in_req = self.request.data.get("documents", None)
            docs_to_add = []
            if docs_in_req:
                docs_to_add = [get_object_or_404(Document, pk=id) for id in docs_in_req]
            docs_to_detach = list(set(assessment.documents.all()) - set(docs_to_add))
            if serializer.is_valid():
                serializer.save(documents=docs_to_add, modified_by=self.request.user)
                for doc in docs_to_detach:
                    assessment.documents.remove(doc)
                    doc.detached = True
                    doc.save()
                return Response(data=serializer.data, status=status.HTTP_200_OK)
        else:
            if serializer.is_valid():
                serializer.save(modified_by=self.request.user)
                return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        assessment = self.get_object()
        if "documents" in self.request.data:
            docs_in_req = self.request.data.get("documents", None)
            docs_to_add = []
            if docs_in_req:
                docs_to_add = [get_object_or_404(Document, pk=id) for id in docs_in_req]
            docs_to_detach = list(set(assessment.documents.all()) - set(docs_to_add))
            serializer.save(documents=docs_to_add, modified_by=self.request.user)
            for doc in docs_to_detach:
                assessment.documents.remove(doc)
                doc.detached = True
                doc.save()
        else:
            serializer.save(modified_by=self.request.user)
        assessment.barrier.save()
