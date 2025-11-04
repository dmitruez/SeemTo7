"""Serializers supporting the custom account flows."""

from __future__ import annotations

from typing import Iterable, List

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from catalog.models import ApparelItem
from .models import AccountRecoveryToken, OneTimeRegistrationToken

User = get_user_model()


class PurchasedItemSerializer(serializers.ModelSerializer):
    """Lightweight representation of a purchased apparel item."""

    collection_name = serializers.CharField(source="collection.name", read_only=True)

    class Meta:
        model = ApparelItem
        fields = (
            "id",
            "name",
            "slug",
            "collection",
            "collection_name",
            "rarity",
            "size",
            "product_url",
            "acquired_at",
        )
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """Public profile information including purchased items."""

    purchased_items = PurchasedItemSerializer(many=True, source="purchased_items")
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "profile_slug",
            "profile_url",
            "purchased_items",
        )
        read_only_fields = fields

    def get_profile_url(self, obj: User) -> str:
        request = self.context.get("request")
        profile_path = obj.profile_url
        if request:
            return request.build_absolute_uri(profile_path)
        return profile_path


class RegistrationTokenCreateSerializer(serializers.Serializer):
    """Validate payload for creating a new registration token."""

    email = serializers.EmailField()
    apparel_item_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
    order_reference = serializers.CharField(required=False, allow_blank=True)

    default_error_messages = {
        "item_claimed": _("Одна из вещей уже закреплена за пользователем."),
    }

    def validate_apparel_item_ids(self, value: Iterable[int]) -> List[int]:
        items = list(
            ApparelItem.objects.filter(id__in=value, owner__isnull=True).values_list(
                "id", flat=True
            )
        )
        missing = set(value) - set(items)
        if missing:
            self.fail("item_claimed")
        return list(items)

    def create_token(self) -> OneTimeRegistrationToken:
        data = self.validated_data
        item_ids = list(data["apparel_item_ids"])
        token = OneTimeRegistrationToken.objects.create(
            email=data["email"],
            order_reference=data.get("order_reference", ""),
            apparel_item_ids=item_ids,
        )
        return token


class RegistrationClaimSerializer(serializers.Serializer):
    """Claim a registration token and create a user account."""

    token = serializers.UUIDField()
    username = serializers.CharField(min_length=3, max_length=150)
    password = serializers.CharField(write_only=True)
    recovery_email = serializers.EmailField(required=False, allow_blank=True)
    recovery_phone = serializers.CharField(required=False, allow_blank=True)

    default_error_messages = {
        "invalid_token": _("Токен не найден или уже использован."),
    }

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate(self, attrs):
        try:
            token = OneTimeRegistrationToken.objects.select_for_update().get(
                token=attrs["token"]
            )
        except OneTimeRegistrationToken.DoesNotExist as exc:  # pragma: no cover - defensive
            raise serializers.ValidationError(self.error_messages["invalid_token"]) from exc
        if not token.is_active:
            raise serializers.ValidationError(self.error_messages["invalid_token"])
        attrs["registration_token"] = token
        return attrs

    def create_user(self) -> User:
        token: OneTimeRegistrationToken = self.validated_data["registration_token"]
        user = User.objects.create_user(
            username=self.validated_data["username"],
            password=self.validated_data["password"],
            email=token.email,
            recovery_email=self.validated_data.get("recovery_email", ""),
            recovery_phone=self.validated_data.get("recovery_phone", ""),
        )
        item_ids = token.apparel_item_ids
        if item_ids:
            ApparelItem.objects.filter(id__in=item_ids).update(owner=user)
        token.mark_claimed(user)
        return user


class RegistrationQRCodeSerializer(serializers.Serializer):
    """Serialize the registration token into an embeddable QR code."""

    token = serializers.UUIDField()

    default_error_messages = {
        "invalid_token": _("Токен не найден."),
    }

    def validate_token(self, value):
        if not OneTimeRegistrationToken.objects.filter(token=value).exists():
            self.fail("invalid_token")
        return value


class AccountRecoveryRequestSerializer(serializers.Serializer):
    """Request a recovery token to reset credentials."""

    identifier = serializers.CharField()

    def get_user(self) -> User | None:
        identifier = self.validated_data["identifier"]
        return User.objects.filter(
            models.Q(username=identifier) | models.Q(email=identifier)
        ).first()

    def create_token(self, user: User) -> AccountRecoveryToken:
        return AccountRecoveryToken.objects.create(user=user)


class AccountRecoveryConfirmSerializer(serializers.Serializer):
    """Validate recovery token usage."""

    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True)

    default_error_messages = {
        "invalid_token": _("Ссылка восстановления недействительна."),
    }

    def validate_new_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate(self, attrs):
        try:
            recovery_token = AccountRecoveryToken.objects.select_related("user").get(
                token=attrs["token"]
            )
        except AccountRecoveryToken.DoesNotExist as exc:  # pragma: no cover - defensive
            raise serializers.ValidationError(self.error_messages["invalid_token"]) from exc
        if not recovery_token.is_active:
            raise serializers.ValidationError(self.error_messages["invalid_token"])
        attrs["recovery_token"] = recovery_token
        return attrs

    def update_password(self) -> User:
        token: AccountRecoveryToken = self.validated_data["recovery_token"]
        user = token.user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        token.mark_used()
        return user
