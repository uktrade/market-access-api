from rest_framework.decorators import api_view, permission_classes
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from api.user.models import Profile, Watchlist
from api.user.serializers import WhoAmISerializer, WatchlistSerializer


@api_view()
@permission_classes([])
def who_am_i(request):
    """Return the current user. This view is behind a login."""
    serializer = WhoAmISerializer(request.user)

    return Response(data=serializer.data)


class WatchlistDetails(generics.RetrieveUpdateDestroyAPIView):
    """
    Handling watchlist items, such as notes
    """

    lookup_field = "pk"
    queryset = Watchlist.objects.all()
    serializer_class = WatchlistSerializer

    def get_queryset(self):
        return self.queryset.filter(id=self.kwargs.get("pk"))

    def perform_update(self, serializer):
        watchlist = self.get_object()
        serializer.save(modified_by=self.request.user)

    # def perform_destroy(self, instance):
    #     instance.archive(self.request.user)
