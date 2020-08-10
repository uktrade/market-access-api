from django.urls import path

from .views import BarrierListDataWorkspaceView, BarrierList


urlpatterns = [
    # TODO: Deprecate `barriers/dataset` when Data Workspace have switched to the new url
    path("barriers/dataset", BarrierListDataWorkspaceView.as_view(), name="dataset-barriers"),
    path("dataset/v1/barriers", BarrierList.as_view(), name="barrier-list"),
]
