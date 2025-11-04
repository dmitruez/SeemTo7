"""Admin registrations for custom user and authentication models."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AccountRecoveryToken, OneTimeRegistrationToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Профиль",
            {
                "fields": (
                    "profile_slug",
                    "recovery_email",
                    "recovery_phone",
                )
            },
        ),
    )
    readonly_fields = ("profile_slug",)
    list_display = BaseUserAdmin.list_display + ("profile_slug",)
    search_fields = BaseUserAdmin.search_fields + ("profile_slug",)


@admin.register(OneTimeRegistrationToken)
class OneTimeRegistrationTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "email", "order_reference", "is_active", "claimed_at")
    list_filter = ("claimed_at",)
    search_fields = ("token", "email", "order_reference")
    readonly_fields = ("apparel_item_ids",)


@admin.register(AccountRecoveryToken)
class AccountRecoveryTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "user", "is_active", "created_at", "used_at")
    list_filter = ("used_at",)
    search_fields = ("token", "user__username", "user__email")
