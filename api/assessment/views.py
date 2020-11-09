from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.response import Response

from api.assessment.models import Assessment, ResolvabilityAssessment, StrategicAssessment
from api.assessment.serializers import (
    AssessmentSerializer,
    ResolvabilityAssessmentSerializer,
    StrategicAssessmentSerializer,
)

from api.barriers.models import Barrier
from api.core.utils import cleansed_username
from api.interactions.models import Document


class BarrierAssessmentDetail(
    generics.CreateAPIView,
    generics.RetrieveUpdateAPIView
):
    """
    Return details of a Barrier Assessment
    Allows the barrier assessment to be created and updated
    """

    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer

    def get_queryset(self):
        barrier_obj = get_object_or_404(Barrier, pk=self.kwargs.get("pk"))
        return self.queryset.filter(barrier=barrier_obj)

    def get_object(self):
        barrier_obj = get_object_or_404(Barrier, pk=self.kwargs.get("pk"))
        # May raise a permission denied
        self.check_object_permissions(self.request, barrier_obj)

        if hasattr(barrier_obj, 'assessment'):
            return barrier_obj.assessment

        raise Http404('No %s matches the given query.' % self.queryset.model._meta.object_name)

    def perform_create(self, serializer):
        barrier_obj = get_object_or_404(Barrier, pk=self.kwargs.get("pk"))

        if hasattr(barrier_obj, 'assessment'):
            raise serializers.ValidationError("Assessment already exists")

        impact = self.request.data.get("impact", "")
        explanation = self.request.data.get("explanation", "")
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


class BarrierAssessmentHistory(generics.GenericAPIView):
    def _format_user(self, user):
        if user is not None:
            return {"id": user.id, "name": cleansed_username(user)}

        return None

    def _assessment_fields_added(self, history_record, fields):
        for field in fields:
            if getattr(history_record, field):
                return field

    def get(self, request, pk):
        barrier = Barrier.barriers.get(id=pk)
        barrier_history = barrier.history.all().order_by("history_date")
        assessment = get_object_or_404(Assessment, barrier=barrier)
        assess_history = assessment.history.all().order_by("history_date")
        status_change = None
        results = []
        old_record = None
        timeline_fields = ["impact", "value_to_economy", "import_market_size", "commercial_value", "export_value"]
        for new_record in assess_history:
            if new_record.history_type == "+":
                field_added = self._assessment_fields_added(new_record, timeline_fields)
                if field_added in timeline_fields:
                    status_change = {
                        "date": new_record.history_date,
                        "model": "assessment",
                        "field": field_added,
                        "old_value": None,
                        "new_value": getattr(new_record, field_added),
                        "user": self._format_user(
                            new_record.history_user
                        ),
                    }
            else:
                if old_record is not None:
                    status_change = None
                    delta = new_record.diff_against(old_record)
                    for change in delta.changes:
                        if change.field in timeline_fields:
                            status_change = {
                                "date": new_record.history_date,
                                "model": "assessment",
                                "field": change.field,
                                "old_value": change.old,
                                "new_value": change.new,
                                "user": self._format_user(
                                    new_record.history_user
                                ),
                            }
            if status_change:
                results.append(status_change)
            old_record = new_record
        response = {"barrier_id": str(pk), "history": results}
        return Response(response, status=status.HTTP_200_OK)


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
