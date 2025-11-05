"""Serializers for the catalog API."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    ApparelItem,
    ApparelItemImage,
    ApparelItemSizeInventory,
    ApparelUnit,
    Collection,
)


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for collection data."""

    total_units = serializers.IntegerField(read_only=True)
    remaining_units = serializers.IntegerField(read_only=True)
    inventory_summary = serializers.SerializerMethodField()

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
            "total_units",
            "remaining_units",
            "inventory_summary",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "total_units",
            "remaining_units",
            "inventory_summary",
        )

    def get_inventory_summary(self, obj: Collection):
        items = getattr(obj, "_prefetched_objects_cache", {}).get("apparel_items")
        if items is None:
            items = list(obj.apparel_items.all())
        return [
            {
                "id": item.id,
                "name": item.name,
                "slug": item.slug,
                "total_units": item.total_units,
                "remaining_units": item.remaining_units,
            }
            for item in items
        ]


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
    """Serializer for apparel items with aggregate inventory data."""

    main_images = ApparelItemImageSerializer(many=True, read_only=True)
    size_inventories = ApparelItemSizeInventorySerializer(many=True, read_only=True)
    total_units = serializers.IntegerField(read_only=True)
    remaining_units = serializers.IntegerField(read_only=True)

    class Meta:
        model = ApparelItem
        fields = (
            "id",
            "name",
            "slug",
            "collection",
            "rarity",
            "main_images",
            "size_inventories",
            "total_units",
            "remaining_units",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "size_inventories",
            "total_units",
            "remaining_units",
            "created_at",
            "updated_at",
        )


class ApparelUnitSerializer(serializers.ModelSerializer):
    """Serializer for individual apparel units."""

    owner = OwnerSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        source="owner",
        write_only=True,
        allow_null=True,
        required=False,
    )
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_slug = serializers.CharField(source="item.slug", read_only=True)
    collection = serializers.PrimaryKeyRelatedField(
        source="item.collection",
        read_only=True,
    )
    collection_name = serializers.CharField(
        source="item.collection.name",
        read_only=True,
    )
    rarity = serializers.CharField(source="item.rarity", read_only=True)

    class Meta:
        model = ApparelUnit
        fields = (
            "id",
            "item",
            "item_name",
            "item_slug",
            "collection",
            "collection_name",
            "rarity",
            "size",
            "access_code",
            "owner",
            "owner_id",
            "assigned_at",
            "qr_code_url",
            "created_at",
        )
        read_only_fields = (
            "id",
            "item",
            "item_name",
            "item_slug",
            "collection",
            "collection_name",
            "rarity",
            "access_code",
            "owner",
            "assigned_at",
            "qr_code_url",
            "created_at",
        )
