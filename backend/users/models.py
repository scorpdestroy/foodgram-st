from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint, CheckConstraint, Q, F
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import EmailValidator
from .constants import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH, NAME_MAX_LENGTH

class User(AbstractUser):
    """Кастомный пользователь: логин — email, username обязателен для фронта."""

    email = models.EmailField(
        "Адрес электронной почты",
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
    )
    username = models.CharField(
        "Имя пользователя",
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        help_text="Уникальный никнейм для отображения в ссылках/UI.",
        validators=[UnicodeUsernameValidator()],
    )
    first_name = models.CharField(
        "Имя",
        max_length=NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=NAME_MAX_LENGTH,
    )
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

class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriber",
        verbose_name="подписчик"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscribing",
        verbose_name="автор"
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "author"],
                name="unique_subscription"
            ),
            CheckConstraint(
                check=~Q(user=F("author")),
                name="prevent_self_subscription"
            ),
        ]
        verbose_name = "подписка"
        verbose_name_plural = "подписки"

    def __str__(self):
        return f"{self.user} ← {self.author}"