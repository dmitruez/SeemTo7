"""Serializers for the catalog API."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    ApparelItem,
    ApparelItemImage,
    ApparelItemSizeInventory,
    Collection,
)


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

    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "profile_slug", "profile_url")
        read_only_fields = fields

    def get_profile_url(self, obj):
        request = self.context.get("request")
        url = obj.profile_url
        if request:
            return request.build_absolute_uri(url)
        return url


class ApparelItemImageSerializer(serializers.ModelSerializer):
    """Serializer for individual apparel gallery images."""

    item = serializers.PrimaryKeyRelatedField(
        queryset=ApparelItem.objects.all(), write_only=True
    )

    class Meta:
        model = ApparelItemImage
        fields = ("id", "item", "image", "position")
        read_only_fields = ("id",)


class ApparelItemSizeInventorySerializer(serializers.ModelSerializer):
    """Representation of inventory counts per size."""

    class Meta:
        model = ApparelItemSizeInventory
        fields = ("size", "quantity_initial", "quantity_remaining")
        read_only_fields = fields


class ApparelItemSerializer(serializers.ModelSerializer):
    """Serializer for apparel items."""

    owner = OwnerSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        source="owner",
        write_only=True,
        allow_null=True,
        required=False,
    )
    main_images = ApparelItemImageSerializer(many=True, read_only=True)
    size_inventories = ApparelItemSizeInventorySerializer(many=True, read_only=True)

    class Meta:
        model = ApparelItem
        fields = (
            "id",
            "name",
            "slug",
            "collection",
            "rarity",
            "main_images",
            "owner",
            "owner_id",
            "access_code",
            "size_inventories",
            "acquired_at",
            "qr_code_url",
        )
        read_only_fields = (
            "id",
            "owner",
            "access_code",
            "size_inventories",
            "acquired_at",
            "qr_code_url",
        )
