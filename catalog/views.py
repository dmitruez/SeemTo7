"""Viewsets exposing the catalog API."""

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ApparelItem, ApparelItemImage, ApparelUnit, Collection
from .serializers import (
    ApparelItemImageSerializer,
    ApparelItemSerializer,
    ApparelUnitSerializer,
    CollectionSerializer,
)


class CollectionViewSet(viewsets.ModelViewSet):
    """CRUD operations for collections."""

    queryset = (
        Collection.objects.all()
        .prefetch_related("apparel_items__units")
        .order_by("name")
    )
    serializer_class = CollectionSerializer


class ApparelItemViewSet(viewsets.ModelViewSet):
    """CRUD operations for apparel items."""

    queryset = (
        ApparelItem.objects.select_related("collection")
        .prefetch_related("size_inventories", "main_images", "units")
        .all()
    )
    serializer_class = ApparelItemSerializer

    def get_serializer_class(self):
        if self.action == "lookup":
            return ApparelUnitSerializer
        return super().get_serializer_class()

    @action(detail=False, url_path=r"lookup/(?P<access_code>[A-Za-z0-9]+)", methods=["get"])
    def lookup(self, request, access_code: str) -> Response:
        """Return apparel item details by its access code."""

        unit = get_object_or_404(
            ApparelUnit.objects.select_related("item", "item__collection", "owner"),
            access_code=access_code,
        )
        serializer = self.get_serializer(unit)
        return Response(serializer.data)


class ApparelItemImageViewSet(viewsets.ModelViewSet):
    """CRUD operations for apparel main images."""

    queryset = ApparelItemImage.objects.select_related("item", "item__collection")
    serializer_class = ApparelItemImageSerializer


class ApparelUnitViewSet(viewsets.ModelViewSet):
    """Operations for individual apparel units."""

    queryset = ApparelUnit.objects.select_related("item", "item__collection", "owner")
    serializer_class = ApparelUnitSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def perform_update(self, serializer):
        owner = self.request.user if self.request.user.is_authenticated else None
        if owner and "owner" not in serializer.validated_data:
            serializer.save(owner=owner)
        else:
            serializer.save()
