"""Initial migration for catalog app."""

from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Collection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                ("release_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="ApparelItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                ("rarity", models.CharField(choices=[("common", "Common"), ("rare", "Rare"), ("epic", "Epic"), ("legendary", "Legendary")], default="common", max_length=32)),
                ("edition_size", models.PositiveIntegerField(help_text="Общий тираж вещи")),
                ("size", models.CharField(choices=[("XS", "XS"), ("S", "S"), ("M", "M"), ("L", "L"), ("XL", "XL"), ("XXL", "XXL")], max_length=3)),
                ("product_url", models.URLField()),
                ("modifications", models.JSONField(blank=True, default=list)),
                ("quantity_remaining", models.PositiveIntegerField(help_text="Количество доступных экземпляров")),
                ("acquired_at", models.DateTimeField(auto_now_add=True)),
                ("collection", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="apparel_items", to="catalog.collection")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="apparel_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-acquired_at",),
                "unique_together": {("collection", "slug")},
            },
        ),
    ]
