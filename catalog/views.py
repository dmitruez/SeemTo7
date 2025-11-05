"""Viewsets exposing the catalog API."""

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ApparelItem, ApparelItemImage, Collection
from .serializers import (
    ApparelItemImageSerializer,
    ApparelItemSerializer,
    CollectionSerializer,
)


class CollectionViewSet(viewsets.ModelViewSet):
    """CRUD operations for collections."""

    queryset = Collection.objects.all().order_by("name")
    serializer_class = CollectionSerializer


class ApparelItemViewSet(viewsets.ModelViewSet):
    """CRUD operations for apparel items."""

    queryset = (
        ApparelItem.objects.select_related("collection", "owner")
        .prefetch_related("size_inventories")
        .all()
    )
    serializer_class = ApparelItemSerializer

    def perform_create(self, serializer):
        owner = self.request.user if self.request.user.is_authenticated else None
        if owner and "owner" not in serializer.validated_data:
            serializer.save(owner=owner)
        else:
            serializer.save()

    @action(detail=False, url_path=r"lookup/(?P<access_code>[A-Za-z0-9]+)", methods=["get"])
    def lookup(self, request, access_code: str) -> Response:
        """Return apparel item details by its access code."""

        item = get_object_or_404(self.get_queryset(), access_code=access_code)
        serializer = self.get_serializer(item)
        return Response(serializer.data)


class ApparelItemImageViewSet(viewsets.ModelViewSet):
    """CRUD operations for apparel main images."""

    queryset = ApparelItemImage.objects.select_related("item", "item__collection")
    serializer_class = ApparelItemImageSerializer
