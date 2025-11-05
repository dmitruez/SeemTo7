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

    @property
    def total_units(self) -> int:
        """Return total number of physical items within the collection."""

        items = getattr(self, "_prefetched_objects_cache", {}).get("apparel_items")
        if items is None:
            items = list(self.apparel_items.all())
        return sum(item.total_units for item in items)

    @property
    def remaining_units(self) -> int:
        """Return remaining unassigned physical items within the collection."""

        items = getattr(self, "_prefetched_objects_cache", {}).get("apparel_items")
        if items is None:
            items = list(self.apparel_items.all())
        return sum(item.remaining_units for item in items)


class ApparelItem(models.Model):
    """A model of clothing within a collection with inventory per size."""

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("collection", "slug")

    def __str__(self) -> str:  # pragma: no cover - trivial representation
        collection_name = str(self.collection)
        return f"{self.name} ({collection_name})"

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
        """Validate model on save and align inventory with collection templates."""

        self.full_clean()
        super().save(*args, **kwargs)
        self._sync_inventory_from_collection()
        self._ensure_units_from_templates()

    @property
    def total_units(self) -> int:
        """Return the number of physical items generated for this apparel."""

        units = getattr(self, "_prefetched_objects_cache", {}).get("units")
        if units is not None:
            return len(units)
        return self.units.count()

    @property
    def remaining_units(self) -> int:
        """Return the number of unassigned physical items."""

        units = getattr(self, "_prefetched_objects_cache", {}).get("units")
        if units is not None:
            return sum(1 for unit in units if unit.owner_id is None)
        return self.units.filter(owner__isnull=True).count()

    def refresh_inventory_for_size(self, size: str) -> None:
        """Synchronise stored inventory numbers for a single size."""

        units = self.units.filter(size=size)
        total = units.count()
        remaining = units.filter(owner__isnull=True).count()

        if not total:
            self.size_inventories.filter(size=size).delete()
            return

        inventory, created = self.size_inventories.get_or_create(
            size=size,
            defaults={
                "quantity_initial": total,
                "quantity_remaining": remaining,
            },
        )
        if not created:
            updated_fields = []
            if inventory.quantity_initial != total:
                inventory.quantity_initial = total
                updated_fields.append("quantity_initial")
            if inventory.quantity_remaining != remaining:
                inventory.quantity_remaining = remaining
                updated_fields.append("quantity_remaining")
            if updated_fields:
                inventory.save(update_fields=updated_fields)

    def _sync_inventory_from_collection(self) -> None:
        """Ensure inventories exist for sizes defined on the parent collection."""

        templates = {
            template.size: template.quantity
            for template in self.collection.size_templates.all()
        }
        existing = {stock.size: stock for stock in self.size_inventories.all()}

        for size, quantity in templates.items():
            stock = existing.get(size)
            if stock:
                updated_fields = []
                if stock.quantity_initial != quantity:
                    stock.quantity_initial = quantity
                    updated_fields.append("quantity_initial")
                if stock.quantity_remaining > quantity:
                    stock.quantity_remaining = quantity
                    updated_fields.append("quantity_remaining")
                if updated_fields:
                    stock.save(update_fields=updated_fields)
            else:
                ApparelItemSizeInventory.objects.create(
                    item=self,
                    size=size,
                    quantity_initial=quantity,
                    quantity_remaining=quantity,
                )

        for size, stock in existing.items():
            if size not in templates:
                stock.delete()

    def _ensure_units_from_templates(self) -> None:
        """Generate physical units for each configured size."""

        templates = {
            template.size: template.quantity
            for template in self.collection.size_templates.all()
        }

        for size, quantity in templates.items():
            existing = self.units.filter(size=size).count()
            missing = quantity - existing
            if missing > 0:
                for _ in range(missing):
                    ApparelUnit.objects.create(item=self, size=size)
            elif missing < 0:
                removable = (
                    self.units.filter(size=size, owner__isnull=True)
                    .order_by("-id")[: abs(missing)]
                )
                removable_ids = list(removable.values_list("id", flat=True))
                if removable_ids:
                    ApparelUnit.objects.filter(id__in=removable_ids).delete()
            self.refresh_inventory_for_size(size)

        extra_sizes = set(
            self.units.values_list("size", flat=True).distinct()
        ) - set(templates.keys())
        for size in extra_sizes:
            removable = self.units.filter(size=size, owner__isnull=True)
            if removable.exists():
                removable.delete()
            self.refresh_inventory_for_size(size)


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


class ApparelUnit(models.Model):
    """A unique physical piece of clothing belonging to an apparel item."""

    item = models.ForeignKey(
        ApparelItem,
        on_delete=models.CASCADE,
        related_name="units",
    )
    size = models.CharField(max_length=3, choices=SizeChoices.choices)
    access_code = models.CharField(
        max_length=16,
        unique=True,
        editable=False,
        help_text="Уникальный код доступа к конкретной вещи",
        default=generate_access_code,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="apparel_units",
        blank=True,
        null=True,
        help_text="Пользователь, которому принадлежит вещь.",
    )
    assigned_at = models.DateTimeField(blank=True, null=True)
    qr_code_url = models.URLField(
        blank=True,
        help_text="Ссылка на QR-код страницы вещи.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("item", "size", "id")

    def __str__(self) -> str:  # pragma: no cover - trivial representation
        return f"{self.item} — {self.size}"

    def get_absolute_url(self) -> str:
        """Return the canonical URL for the apparel unit detail endpoint."""

        return reverse("apparelitem-lookup", kwargs={"access_code": self.access_code})

    @property
    def is_available(self) -> bool:
        """Return True when the unit is not assigned to a user."""

        return self.owner_id is None

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Persist the unit and synchronise auxiliary fields."""

        from django.utils import timezone

        creating = self.pk is None
        previous_owner_id = None
        previous_size = None
        if not creating:
            previous = type(self).objects.get(pk=self.pk)
            previous_owner_id = previous.owner_id
            previous_size = previous.size

        super().save(*args, **kwargs)

        new_qr = self._build_qr_url()
        if self.qr_code_url != new_qr:
            type(self).objects.filter(pk=self.pk).update(qr_code_url=new_qr)
            self.qr_code_url = new_qr

        if self.owner_id and self.owner_id != previous_owner_id:
            assigned_at = timezone.now()
        elif previous_owner_id and not self.owner_id:
            assigned_at = None
        else:
            assigned_at = self.assigned_at

        if assigned_at != self.assigned_at:
            type(self).objects.filter(pk=self.pk).update(assigned_at=assigned_at)
            self.assigned_at = assigned_at

        sizes_to_refresh = {self.size}
        if previous_size and previous_size != self.size:
            sizes_to_refresh.add(previous_size)

        for size in sizes_to_refresh:
            self.item.refresh_inventory_for_size(size)

    def delete(self, *args: Any, **kwargs: Any) -> None:
        """Ensure inventory numbers are updated when the unit is removed."""

        size = self.size
        item = self.item
        super().delete(*args, **kwargs)
        item.refresh_inventory_for_size(size)

    def _build_qr_url(self) -> str:
        """Return a hosted QR image that encodes the unit page."""

        item_path = self.get_absolute_url()
        encoded = quote(item_path, safe="")
        return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"


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
