"""Database models describing collectible apparel."""

from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


def generate_access_code() -> str:
    """Generate a short hexadecimal token for secure lookups."""

    return secrets.token_hex(4).upper()


class SizeChoices(models.TextChoices):
    """Standardised clothing sizes used across collections."""

    XS = "XS", "XS"
    S = "S", "S"
    M = "M", "M"
    L = "L", "L"
    XL = "XL", "XL"
    XXL = "XXL", "XXL"


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
        return str(self.name)

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

    Size = SizeChoices

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
    access_code = models.CharField(
        max_length=16,
        unique=True,
        editable=False,
        help_text="Уникальный код доступа к подробной информации о вещи",
        default=generate_access_code,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="apparel_items",
        blank=True,
        null=True,
        help_text="Пользователь, которому принадлежит вещь.",
    )
    acquired_at = models.DateTimeField(auto_now_add=True)
    qr_code_url = models.URLField(
        blank=True,
        help_text="Ссылка на QR-код страницы вещи.",
    )

    class Meta:
        ordering = ("-acquired_at",)
        unique_together = ("collection", "slug")

    def __str__(self) -> str:  # pragma: no cover - trivial representation
        collection_name = str(self.collection)
        return f"{self.name} ({collection_name})"

    def get_absolute_url(self) -> str:
        """Return the canonical URL for the apparel detail endpoint."""

        return reverse("apparelitem-lookup", kwargs={"access_code": self.access_code})

    def clean(self) -> None:
        """Ensure the parent collection defines size templates."""

        super().clean()
        if not self.collection.size_templates.exists():
            raise ValidationError(
                {
                    "collection": "Selected collection must define size allocations before items can be created."
                }
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Validate model on save and refresh the QR link."""

        self.full_clean()
        super().save(*args, **kwargs)
        self._sync_inventory_from_collection()
        new_qr = self._build_qr_url()
        if self.qr_code_url != new_qr:
            type(self).objects.filter(pk=self.pk).update(qr_code_url=new_qr)
            self.qr_code_url = new_qr

    def _build_qr_url(self) -> str:
        """Return a hosted QR image that encodes the item page."""

        item_path = self.get_absolute_url()
        encoded = quote(item_path, safe="")
        return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"

    def _sync_inventory_from_collection(self) -> None:
        """Ensure the inventory mirrors the collection template."""

        templates = {template.size: template for template in self.collection.size_templates.all()}
        existing = {stock.size: stock for stock in self.size_inventories.all()}

        for size, template in templates.items():
            stock = existing.get(size)
            if stock:
                updated_fields = []
                if stock.quantity_initial != template.quantity:
                    stock.quantity_initial = template.quantity
                    updated_fields.append("quantity_initial")
                if stock.quantity_remaining > template.quantity:
                    stock.quantity_remaining = template.quantity
                    updated_fields.append("quantity_remaining")
                if updated_fields:
                    stock.save(update_fields=updated_fields)
            else:
                ApparelItemSizeInventory.objects.create(
                    item=self,
                    size=size,
                    quantity_initial=template.quantity,
                    quantity_remaining=template.quantity,
                )

        for size, stock in existing.items():
            if size not in templates:
                stock.delete()

class CollectionSizeTemplate(models.Model):
    """Immutable size allocation used to seed apparel inventory."""

    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="size_templates",
    )
    size = models.CharField(max_length=3, choices=SizeChoices.choices)
    quantity = models.PositiveIntegerField(help_text="Предустановленное количество вещей этого размера")

    class Meta:
        unique_together = ("collection", "size")
        ordering = ("collection", "size")

    def __str__(self) -> str:  # pragma: no cover - trivial representation
        return f"{self.collection} — {self.size}"


class ApparelItemSizeInventory(models.Model):
    """Actual inventory for each size of an apparel item."""

    item = models.ForeignKey(
        ApparelItem,
        on_delete=models.CASCADE,
        related_name="size_inventories",
    )
    size = models.CharField(max_length=3, choices=SizeChoices.choices)
    quantity_initial = models.PositiveIntegerField()
    quantity_remaining = models.PositiveIntegerField()

    class Meta:
        unique_together = ("item", "size")
        ordering = ("size", "id")

    def __str__(self) -> str:  # pragma: no cover - trivial representation
        item_name = str(self.item)
        return f"{item_name} — {self.size}"


class ApparelItemImage(models.Model):
    """Primary gallery images for an apparel item."""

    item = models.ForeignKey(
        ApparelItem,
        on_delete=models.CASCADE,
        related_name="main_images",
    )
    image = models.ImageField(upload_to="apparel/main/")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("position", "id")

    def __str__(self) -> str:  # pragma: no cover - trivial representation
        item_name = str(self.item)
        return f"{item_name} — {self.position}"
