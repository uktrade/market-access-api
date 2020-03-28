"""Document test views."""

from .models import MyEntityDocument
from .serializers import MyEntityDocumentSerializer
from api.documents.views import BaseEntityDocumentModelViewSet


class MyEntityDocumentViewSet(BaseEntityDocumentModelViewSet):
    """MyEntityDocument ViewSet."""

    serializer_class = MyEntityDocumentSerializer
    queryset = MyEntityDocument.objects.all()
