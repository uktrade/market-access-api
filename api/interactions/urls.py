from django.urls import path

from api.interactions.views import DocumentViewSet


document_collection = DocumentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

document_item = DocumentViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy',
})

document_callback = DocumentViewSet.as_view({
    'post': 'upload_complete_callback',
})

document_download = DocumentViewSet.as_view({
    'get': 'download',
})

urlpatterns = [
    path(
        'documents',
        document_collection,
        name='barrier-documents',
    ),
    path(
        'documents/<uuid:entity_document_pk>',
        document_item,
        name='barrier-document-item',
    ),
    path(
        'documents/<uuid:entity_document_pk>/upload-callback',
        document_callback,
        name='barrier-document-item-callback',
    ),
    path(
        'documents/<uuid:entity_document_pk>/download',
        document_download,
        name='barrier-document-item-download',
    ),
]
