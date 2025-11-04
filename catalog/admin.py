"""Admin configuration for catalog models."""

from django.contrib import admin

from .models import ApparelItem, ApparelItemImage, Collection


class ApparelItemImageInline(admin.TabularInline):
    model = ApparelItemImage
    extra = 1
    fields = ("image", "position")
    ordering = ("position",)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "release_date", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ApparelItem)
class ApparelItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "collection",
        "rarity",
        "size",
        "edition_size",
        "quantity_remaining",
        "owner",
        "acquired_at",
    )
    list_filter = ("collection", "rarity", "size")
    search_fields = ("name", "slug", "collection__name", "owner__username")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (ApparelItemImageInline,)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "collection",
                    "rarity",
                    "size",
                    "edition_size",
                    "quantity_remaining",
                    "owner",
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "product_url",
                    "background_image",
                    "header_image",
                )
            },
        ),
        (
            "Дополнительно",
            {"fields": ("modifications",)},
        ),
    )
