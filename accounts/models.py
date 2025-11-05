"""User related models providing QR encoded profile links."""

from __future__ import annotations

import uuid
from typing import Iterable
from urllib.parse import quote

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """Custom user model identified by phone number and nickname."""

    phone_number = models.CharField(
        max_length=32,
        unique=True,
        help_text="Основной номер телефона пользователя.",
    )
    profile_slug = models.SlugField(
        max_length=64,
        unique=True,
        blank=True,
        help_text="Уникальная ссылка на профиль пользователя.",
    )
    qr_code_url = models.URLField(
        blank=True,
        help_text="Ссылка на QR-код профиля пользователя.",
    )

    class Meta(AbstractUser.Meta):
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    REQUIRED_FIELDS = ["phone_number"]

    def save(self, *args, **kwargs):  # type: ignore[override]
        needs_slug = not self.profile_slug
        if needs_slug:
            self.profile_slug = self._generate_profile_slug()
        self.qr_code_url = self._build_qr_url()
        super().save(*args, **kwargs)

    def _generate_profile_slug(self) -> str:
        """Return a unique short slug for the profile URL."""

        while True:
            candidate = uuid.uuid4().hex[:12]
            if not type(self).objects.filter(profile_slug=candidate).exists():
                return candidate

    def _build_qr_url(self) -> str:
        """Return a hosted QR image that encodes the profile link."""

        profile_path = reverse(
            "accounts:profile-detail", kwargs={"profile_slug": self.profile_slug}
        )
        encoded = quote(profile_path, safe="")
        return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"

    @property
    def profile_url(self) -> str:
        """Return the absolute URL to the public profile."""

        return reverse("accounts:profile-detail", kwargs={"profile_slug": self.profile_slug})

    @property
    def purchased_items(self) -> Iterable["catalog.ApparelUnit"]:
        """Return a queryset of apparel units assigned to the user."""

        return self.apparel_units.select_related("item", "item__collection")
