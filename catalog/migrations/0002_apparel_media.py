"""Add media fields for apparel items."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="apparelitem",
            name="background_image",
            field=models.ImageField(
                blank=True,
                help_text="Фоновое изображение для карточки вещи",
                null=True,
                upload_to="apparel/backgrounds/",
            ),
        ),
        migrations.AddField(
            model_name="apparelitem",
            name="header_image",
            field=models.ImageField(
                blank=True,
                help_text="Изображение для шапки вещи",
                null=True,
                upload_to="apparel/headers/",
            ),
        ),
        migrations.CreateModel(
            name="ApparelItemImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="apparel/main/")),
                ("position", models.PositiveIntegerField(default=0)),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="main_images",
                        to="catalog.apparelitem",
                    ),
                ),
            ],
            options={
                "ordering": ("position", "id"),
            },
        ),
    ]
