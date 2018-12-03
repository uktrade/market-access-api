"""Document test views."""
from oauth2_provider.contrib.rest_framework.permissions import (
    IsAuthenticatedOrTokenHasScope,
)

from api.documents.test.my_entity_document.models import MyEntityDocument
from api.documents.test.my_entity_document.serializers import MyEntityDocumentSerializer
from api.documents.views import BaseEntityDocumentModelViewSet


class MyEntityDocumentViewSet(BaseEntityDocumentModelViewSet):
    """MyEntityDocument ViewSet."""

    serializer_class = MyEntityDocumentSerializer
    queryset = MyEntityDocument.objects.all()
