"""Serializers supporting the simplified account flow."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from catalog.models import ApparelUnit

User = get_user_model()


class PurchasedItemSerializer(serializers.ModelSerializer):
    """Lightweight representation of a purchased apparel unit."""

    item_name = serializers.CharField(source="item.name", read_only=True)
    item_slug = serializers.CharField(source="item.slug", read_only=True)
    collection = serializers.PrimaryKeyRelatedField(
        source="item.collection",
        read_only=True,
    )
    collection_name = serializers.CharField(source="item.collection.name", read_only=True)
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
            "assigned_at",
            "qr_code_url",
        )
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """Public profile information including purchased items."""

    purchased_items = PurchasedItemSerializer(
        source="apparel_units", many=True, read_only=True
    )
    profile_url = serializers.SerializerMethodField()
    nickname = serializers.CharField(source="username", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "nickname",
            "phone_number",
            "profile_slug",
            "profile_url",
            "qr_code_url",
            "purchased_items",
        )
        read_only_fields = fields

    def get_profile_url(self, obj: User) -> str:
        request = self.context.get("request")
        profile_path = obj.profile_url
        if request:
            return request.build_absolute_uri(profile_path)
        return profile_path


class SimpleRegistrationSerializer(serializers.ModelSerializer):
    """Serializer that creates a user using a phone number and nickname."""

    nickname = serializers.CharField(source="username", max_length=150)

    class Meta:
        model = User
        fields = ("nickname", "phone_number")

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_unusable_password()
        user.save()
        return user

    def to_representation(self, instance):
        serializer = UserProfileSerializer(instance, context=self.context)
        return serializer.data
