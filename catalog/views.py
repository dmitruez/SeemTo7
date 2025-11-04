"""Viewsets exposing the catalog API."""

from rest_framework import viewsets

from .models import ApparelItem, Collection
from .serializers import ApparelItemSerializer, CollectionSerializer


class CollectionViewSet(viewsets.ModelViewSet):
    """CRUD operations for collections."""

    queryset = Collection.objects.all().order_by("name")
    serializer_class = CollectionSerializer


class ApparelItemViewSet(viewsets.ModelViewSet):
    """CRUD operations for apparel items."""

    queryset = ApparelItem.objects.select_related("collection", "owner").all()
    serializer_class = ApparelItemSerializer

    def perform_create(self, serializer):
        owner = self.request.user if self.request.user.is_authenticated else None
        if owner and "owner" not in serializer.validated_data:
            serializer.save(owner=owner)
        else:
            serializer.save()
