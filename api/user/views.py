from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.user.serializers import WhoAmISerializer


@api_view()
@permission_classes([])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    serializer = WhoAmISerializer(request.user)

    return Response(data=serializer.data)


class BarrierInteractionList(generics.ListCreateAPIView):
    """
    Handling Barrier interactions, such as notes
    """

    queryset = Interaction.objects.all()
    serializer_class = InteractionSerializer

    def get_queryset(self):
        return self.queryset.filter(barrier_id=self.kwargs.get("pk"))

    def perform_create(self, serializer):
        barrier_obj = get_object_or_404(BarrierInstance, pk=self.kwargs.get("pk"))
        kind = self.request.data.get("kind", BARRIER_INTERACTION_TYPE["COMMENT"])
        docs_in_req = self.request.data.get("documents", None)
        documents = []
        if docs_in_req:
            documents = [get_object_or_404(Document, pk=id) for id in docs_in_req]
        serializer.save(
            barrier=barrier_obj,
            kind=kind,
            documents=documents,
            created_by=self.request.user,
        )
        barrier_obj.save()
