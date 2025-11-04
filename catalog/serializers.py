"""Serializers for the catalog API."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ApparelItem, Collection


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for collection data."""

    class Meta:
        model = Collection
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "release_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class OwnerSerializer(serializers.ModelSerializer):
    """Simple representation of the user owning an apparel item."""

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email")
        read_only_fields = fields


class ApparelItemSerializer(serializers.ModelSerializer):
    """Serializer for apparel items."""

    owner = OwnerSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(), source="owner", write_only=True
    )

    class Meta:
        model = ApparelItem
        fields = (
            "id",
            "name",
            "slug",
            "collection",
            "rarity",
            "edition_size",
            "size",
            "product_url",
            "modifications",
            "owner",
            "owner_id",
            "quantity_remaining",
            "acquired_at",
        )
        read_only_fields = ("id", "owner", "acquired_at")
