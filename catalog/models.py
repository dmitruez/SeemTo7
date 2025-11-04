"""Database models describing collectible apparel."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Collection(models.Model):
    """A collection of limited edition apparel items."""

    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    release_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover - trivial representation
        return self.name

    def get_absolute_url(self) -> str:
        """Return the canonical URL for the collection detail endpoint."""

        return reverse("collection-detail", kwargs={"pk": self.pk})


class ApparelItem(models.Model):
    """Individual apparel purchased by a user."""

    class Rarity(models.TextChoices):
        COMMON = "common", "Common"
        RARE = "rare", "Rare"
        EPIC = "epic", "Epic"
        LEGENDARY = "legendary", "Legendary"

    class Size(models.TextChoices):
        XS = "XS", "XS"
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"
        XXL = "XXL", "XXL"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="apparel_items",
    )
    rarity = models.CharField(
        max_length=32,
        choices=Rarity.choices,
        default=Rarity.COMMON,
    )
    edition_size = models.PositiveIntegerField(help_text="Общий тираж вещи")
    size = models.CharField(max_length=3, choices=Size.choices)
    product_url = models.URLField()
    modifications = models.JSONField(default=list, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="apparel_items",
    )
    quantity_remaining = models.PositiveIntegerField(
        help_text="Количество доступных экземпляров",
    )
    acquired_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-acquired_at",)
        unique_together = ("collection", "slug")

    def __str__(self) -> str:  # pragma: no cover - trivial representation
        return f"{self.name} ({self.collection.name})"

    def get_absolute_url(self) -> str:
        """Return the canonical URL for the apparel detail endpoint."""

        return reverse("apparelitem-detail", kwargs={"pk": self.pk})

    def clean(self) -> None:
        """Ensure remaining quantity does not exceed edition size."""

        super().clean()
        if self.quantity_remaining > self.edition_size:
            raise ValidationError(
                {"quantity_remaining": "Remaining quantity cannot exceed edition size."}
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Validate model on save."""

        self.full_clean()
        super().save(*args, **kwargs)
