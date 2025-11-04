"""Admin registrations for the simplified user model."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Профиль",
            {
                "fields": (
                    "phone_number",
                    "profile_slug",
                    "qr_code_url",
                )
            },
        ),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone_number",),
            },
        ),
    )
    readonly_fields = ("profile_slug", "qr_code_url")
    list_display = BaseUserAdmin.list_display + ("phone_number", "profile_slug")
    search_fields = BaseUserAdmin.search_fields + ("phone_number", "profile_slug")
