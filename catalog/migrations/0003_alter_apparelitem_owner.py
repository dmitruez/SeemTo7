"""Allow apparel items to be unattached until a QR token is claimed."""

from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_apparel_media"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="apparelitem",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                help_text="Пользователь, которому принадлежит вещь.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="apparel_items",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
