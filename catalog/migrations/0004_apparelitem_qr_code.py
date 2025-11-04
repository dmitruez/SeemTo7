"""Add QR code field to apparel items."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_alter_apparelitem_owner"),
    ]

    operations = [
        migrations.AddField(
            model_name="apparelitem",
            name="qr_code_url",
            field=models.URLField(
                blank=True,
                help_text="Ссылка на QR-код страницы вещи.",
            ),
        ),
    ]
