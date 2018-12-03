# import json

# from django.conf import settings
# from django.contrib.auth.models import User
# from django.db import transaction
# from django.shortcuts import get_object_or_404
# from django.utils import timezone

# from rest_framework import generics, status
# from rest_framework.decorators import permission_classes
# from rest_framework.response import Response

# from api.barriers.models import (
#     BarrierContributor,
#     BarrierInstance,
#     BarrierStatus,
# )
# from api.metadata.constants import (
#     REPORT_STATUS,
#     CONTRIBUTOR_TYPE
# )
# from api.metadata.models import BarrierType
# from api.reports.serializers import ReportSerializer, ReportStageSerializer


# class ReportBase(object):
#     def _update_stages(self, serializer, user):
#         report_id = serializer.data.get("id")
#         report = Report.objects.get(id=report_id)
#         progress = report.current_stage()
#         for new_stage, new_status in progress:
#             try:
#                 report_stage = ReportStage.objects.get(report=report, stage=new_stage)
#                 report_stage.status = new_status
#                 report_stage.save()
#             except ReportStage.DoesNotExist:
#                 ReportStage(
#                     report=report, stage=new_stage, status=new_status
#                 ).save()
#             if settings.DEBUG is False:
#                 report_stage = ReportStage.objects.get(report=report, stage=new_stage)
#                 report_stage.user = user
#                 report_stage.save()


# class ReportList(ReportBase, generics.ListCreateAPIView):
#     queryset = Report.objects.all()
#     serializer_class = ReportSerializer

#     def get_queryset(self):
#         if self.kwargs["status"] is not None:
#             return self.queryset.filter(status=self.kwargs["status"])
#         return self.queryset

#     @transaction.atomic()
#     def perform_create(self, serializer):
#         if settings.DEBUG is False:
#             serializer.save(created_by=self.request.user)
#         else:
#             serializer.save()
#         self._update_stages(serializer, self.request.user)


# class ReportDetail(ReportBase, generics.RetrieveUpdateAPIView):

#     lookup_field = "pk"
#     queryset = Report.objects.all()
#     serializer_class = ReportSerializer

#     @transaction.atomic()
#     def perform_update(self, serializer):
#         if serializer.validated_data.get("problem_status", None) == 3:
#             serializer.validated_data["is_emergency"] = None
#         if serializer.validated_data.get("is_politically_sensitive", None) is False:
#             serializer.validated_data["political_sensitivity_summary"] = None
#         if serializer.validated_data.get("is_commercially_sensitive", None) is False:
#             serializer.validated_data["commercial_sensitivity_summary"] = None
#         if self.request.data.get("barrier_type", None) is not None:
#             barrier_type = get_object_or_404(BarrierType, pk=self.request.data.get("barrier_type"))
#             serializer.save(barrier_type=barrier_type)
#         else:
#             serializer.save()
#         self._update_stages(serializer, self.request.user)


# class ReportStagesList(generics.ListCreateAPIView):

#     queryset = ReportStage.objects.all()
#     serializer_class = ReportStageSerializer

#     def get_queryset(self):
#         return self.queryset.filter(report_id=self.kwargs.get("report_pk"))

#     def perform_create(self, serializer):
#         report_obj = get_object_or_404(Report, pk=self.kwargs.get("report_pk"))
#         stage_obj = get_object_or_404(ReportStage, pk=self.request.data.get("stage"))
#         if settings.DEBUG is False:
#             serializer.save(
#                 report=report_obj, stage=stage_obj, created_by=self.request.user
#             )
#         else:
#             serializer.save(report=report_obj, stage=stage_obj)


# class ReportStageUpdate(generics.RetrieveUpdateAPIView):
#     queryset = ReportStage.objects.all()
#     serializer_class = ReportStageSerializer

#     def get_object(self):
#         return get_object_or_404(
#             self.get_queryset(),
#             report_id=self.kwargs.get("report_pk"),
#             pk=self.kwargs.get("pk"),
#         )


# class ReportSubmit(generics.UpdateAPIView):

#     queryset = Report.objects.all()
#     serializer_class = ReportSerializer

#     @transaction.atomic()
#     def perform_update(self, serializer):
#         """
#         Validates report for mandatory fields
#         Changes status of the report
#         Creates a Barrier Instance out of the report
#         Sets up default status
#         Sets up contributor where appropriate
#         """
#         # validate and complete a report
#         report = self.get_object()
#         report.complete()

#         # create a new barrier or update existing one
#         try:
#             barrier = BarrierInstance.objects.get(report_id=report.id)
#             # barrier.barrier_type = report.barrier_type,
#             # barrier.summary = report.summary,
#             # barrier.estimated_loss_range = report.estimated_loss_range,
#             # barrier.impact_summary = report.impact_summary,
#             # barrier.other_companies_affected = report.other_companies_affected,
#             # barrier.has_legal_infringement = report.has_legal_infringement,
#             # barrier.wto_infringement = report.wto_infringement,
#             # barrier.fta_infringement = report.fta_infringement,
#             # barrier.other_infringement = report.other_infringement,
#             # barrier.infringement_summary = report.infringement_summary,
#         except BarrierInstance.DoesNotExist:
#             BarrierInstance(
#                 report=report,
#                 barrier_type=report.barrier_type,
#                 summary=report.problem_description,
#                 estimated_loss_range=report.estimated_loss_range,
#                 impact_summary=report.problem_impact,
#                 other_companies_affected=report.other_companies_affected,
#                 has_legal_infringement=report.has_legal_infringement,
#                 wto_infringement=report.wto_infringement,
#                 fta_infringement=report.fta_infringement,
#                 other_infringement=report.other_infringement,
#                 infringement_summary=report.infringement_summary,
#                 reported_on = report.created_on
#             ).save()
#             if settings.DEBUG is False:
#                 barrier = BarrierInstance.objects.get(report_id=report.id)
#                 barrier.created_by = self.request.user
#                 barrier.save()

#         # sort out barrier status
#         if report.is_resolved:
#             barrier_new_status = 4 # Resolved
#         else:
#             barrier_new_status = 2 # Assesment
#         barrier = BarrierInstance.objects.get(report_id=report.id)

#         try:
#             barrier_status = BarrierStatus.objects.get(barrier=barrier, status=barrier_new_status)
#         except BarrierStatus.DoesNotExist:
#             BarrierStatus(
#                 barrier=barrier,
#                 status=barrier_new_status,
#                 status_date=timezone.now()
#             ).save()
#             if settings.DEBUG is False:
#                 barrier_status = BarrierStatus.objects.get(barrier=barrier, status=barrier_new_status)
#                 barrier_status.created_by = self.request.user
#                 barrier_status.save()

#         # sort out contributors
#         if settings.DEBUG is False:
#             if report.support_type == 2:
#                 try:
#                     BarrierContributor.objects.get(
#                         barrier=barrier,
#                         contributor=report.created_by,
#                         kind=CONTRIBUTOR_TYPE['LEAD'],
#                         is_active=True
#                     )
#                 except BarrierContributor.DoesNotExist:
#                     BarrierContributor(
#                         barrier=barrier,
#                         contributor=report.created_by,
#                         kind=CONTRIBUTOR_TYPE['LEAD'],
#                         created_by=self.request.user
#                     ).save()
