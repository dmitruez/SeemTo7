"""User and authentication related models."""

from __future__ import annotations

import uuid
from typing import Iterable

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


class User(AbstractUser):
    """Custom user model with profile link and recovery helpers."""

    profile_slug = models.SlugField(
        max_length=64,
        unique=True,
        blank=True,
        help_text="Уникальная ссылка на профиль пользователя.",
    )
    recovery_email = models.EmailField(
        blank=True,
        help_text="Резервный email для восстановления аккаунта.",
    )
    recovery_phone = models.CharField(
        max_length=32,
        blank=True,
        help_text="Резервный телефон для восстановления аккаунта.",
    )

    class Meta(AbstractUser.Meta):
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def save(self, *args, **kwargs):  # type: ignore[override]
        if not self.profile_slug:
            self.profile_slug = self._generate_profile_slug()
        super().save(*args, **kwargs)

    def _generate_profile_slug(self) -> str:
        """Return a unique short slug for the profile URL."""

        while True:
            candidate = uuid.uuid4().hex[:12]
            if not type(self).objects.filter(profile_slug=candidate).exists():
                return candidate

    @property
    def profile_url(self) -> str:
        """Return the absolute URL to the public profile."""

        return reverse("accounts:profile-detail", kwargs={"slug": self.profile_slug})

    @property
    def purchased_items(self) -> Iterable["catalog.ApparelItem"]:
        """Return a queryset of items the user purchased."""

        return self.apparel_items.select_related("collection")


class OneTimeRegistrationToken(models.Model):
    """A QR powered one-time link that creates a customer account."""

    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(help_text="Почта, на которую отправляется ссылка регистрации.")
    apparel_item_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="Список идентификаторов вещей, которые клиент получит после активации.",
    )
    order_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Внутренний идентификатор покупки.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    claimed_at = models.DateTimeField(blank=True, null=True)
    claimed_user = models.ForeignKey(
        "User",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="registration_tokens",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "QR токен регистрации"
        verbose_name_plural = "QR токены регистрации"

    def save(self, *args, **kwargs):  # type: ignore[override]
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        """Whether the token can still be used to create an account."""

        if self.claimed_at:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def mark_claimed(self, user: User) -> None:
        """Mark the token as claimed by a user."""

        self.claimed_user = user
        self.claimed_at = timezone.now()
        self.save(update_fields=["claimed_user", "claimed_at"])


class AccountRecoveryToken(models.Model):
    """Single-use token that allows resetting account credentials."""

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="recovery_tokens",
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    used_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Токен восстановления"
        verbose_name_plural = "Токены восстановления"

    def save(self, *args, **kwargs):  # type: ignore[override]
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        if self.used_at:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def mark_used(self) -> None:
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
