"""Document test views."""

from api.documents.views import BaseEntityDocumentModelViewSet

from .models import MyEntityDocument
from .serializers import MyEntityDocumentSerializer


class MyEntityDocumentViewSet(BaseEntityDocumentModelViewSet):
    """MyEntityDocument ViewSet."""

    serializer_class = MyEntityDocumentSerializer
    queryset = MyEntityDocument.objects.all()
