from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import EmailValidator
from django.db import models


class User(AbstractUser):
    """Кастомный пользователь: логин — email,
    username обязателен для фронта."""

    email = models.EmailField(
        "Адрес электронной почты",
        unique=True,
        validators=[EmailValidator()],
        max_length=254,
    )
    username = models.CharField(
        "Имя пользователя",
        max_length=150,
        unique=True,
        help_text="Уникальный никнейм для отображения в ссылках/UI.",
        validators=[UnicodeUsernameValidator()],
    )
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)
    avatar = models.ImageField(
        "Аватар",
        upload_to="avatars/",
        blank=True,
        null=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username", "first_name", "last_name")

    class Meta:
        ordering = ("id",)
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return f"{self.username} ({self.email})"
