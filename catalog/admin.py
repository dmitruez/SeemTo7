"""Admin configuration for catalog models."""

from django.contrib import admin

from .models import (
    ApparelItem,
    ApparelItemImage,
    ApparelItemSizeInventory,
    Collection,
    CollectionSizeTemplate,
)


class ApparelItemImageInline(admin.TabularInline):
    model = ApparelItemImage
    extra = 1
    fields = ("image", "position")
    ordering = ("position",)


class CollectionSizeTemplateInline(admin.TabularInline):
    model = CollectionSizeTemplate
    extra = 0
    min_num = 1
    fields = ("size", "quantity")
    can_delete = False


class ApparelItemSizeInventoryInline(admin.TabularInline):
    model = ApparelItemSizeInventory
    extra = 0
    fields = ("size", "quantity_initial", "quantity_remaining")
    readonly_fields = fields
    can_delete = False
    ordering = ("size",)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "release_date", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (CollectionSizeTemplateInline,)


@admin.register(ApparelItem)
class ApparelItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "collection",
        "rarity",
        "access_code",
        "owner",
        "acquired_at",
    )
    list_filter = ("collection", "rarity", "size_inventories__size")
    search_fields = (
        "name",
        "slug",
        "collection__name",
        "owner__username",
        "access_code",
    )
    prepopulated_fields = {"slug": ("name",)}
    inlines = (ApparelItemSizeInventoryInline, ApparelItemImageInline)
    readonly_fields = ("access_code", "qr_code_url")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "collection",
                    "rarity",
                    "owner",
                    "access_code",
                    "qr_code_url",
                )
            },
        ),
    )
