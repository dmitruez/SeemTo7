"""Admin configuration for catalog models."""

from django.contrib import admin

from .models import (
    ApparelItem,
    ApparelItemImage,
    ApparelItemSizeInventory,
    ApparelUnit,
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


class ApparelUnitInline(admin.TabularInline):
    model = ApparelUnit
    extra = 0
    fields = ("size", "access_code", "owner", "assigned_at", "qr_code_url")
    readonly_fields = ("access_code", "assigned_at", "qr_code_url")


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
        "total_units",
        "remaining_units",
    )
    list_filter = ("collection", "rarity", "size_inventories__size")
    search_fields = (
        "name",
        "slug",
        "collection__name",
    )
    prepopulated_fields = {"slug": ("name",)}
    inlines = (ApparelItemSizeInventoryInline, ApparelUnitInline, ApparelItemImageInline)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "collection",
                    "rarity",
                )
            },
        ),
    )


@admin.register(ApparelUnit)
class ApparelUnitAdmin(admin.ModelAdmin):
    list_display = (
        "item",
        "size",
        "access_code",
        "owner",
        "is_available",
        "assigned_at",
    )
    list_filter = ("item__collection", "size", "owner")
    search_fields = (
        "access_code",
        "item__name",
        "item__collection__name",
        "owner__username",
    )
    readonly_fields = ("access_code", "qr_code_url", "assigned_at", "created_at")

    def is_available(self, obj):
        return obj.is_available

    is_available.boolean = True
