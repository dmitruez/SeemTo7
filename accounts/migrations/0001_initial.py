"""Initial migration for the accounts app."""

from __future__ import annotations

import uuid

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(
                    default=False,
                    help_text="Designates that this user has all permissions without explicitly assigning them.",
                    verbose_name="superuser status",
                )),
                ("username", models.CharField(
                    error_messages={"unique": "A user with that username already exists."},
                    help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                    max_length=150,
                    unique=True,
                    validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                    verbose_name="username",
                )),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email address")),
                ("is_staff", models.BooleanField(
                    default=False,
                    help_text="Designates whether the user can log into this admin site.",
                    verbose_name="staff status",
                )),
                ("is_active", models.BooleanField(
                    default=True,
                    help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                    verbose_name="active",
                )),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("profile_slug", models.SlugField(blank=True, help_text="Уникальная ссылка на профиль пользователя.", max_length=64, unique=True)),
                ("recovery_email", models.EmailField(blank=True, help_text="Резервный email для восстановления аккаунта.", max_length=254)),
                ("recovery_phone", models.CharField(blank=True, help_text="Резервный телефон для восстановления аккаунта.", max_length=32)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Пользователь",
                "verbose_name_plural": "Пользователи",
                "abstract": False,
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="OneTimeRegistrationToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("email", models.EmailField(help_text="Почта, на которую отправляется ссылка регистрации.", max_length=254)),
                ("apparel_item_ids", models.JSONField(blank=True, default=list, help_text="Список идентификаторов вещей, которые клиент получит после активации.")),
                ("order_reference", models.CharField(blank=True, help_text="Внутренний идентификатор покупки.", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("claimed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "claimed_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="registration_tokens",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "verbose_name": "QR токен регистрации",
                "verbose_name_plural": "QR токены регистрации",
            },
        ),
        migrations.CreateModel(
            name="AccountRecoveryToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recovery_tokens", to="accounts.user"),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "verbose_name": "Токен восстановления",
                "verbose_name_plural": "Токены восстановления",
            },
        ),
    ]
