from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from users.models import User

from .constants import NAME_MAX_LENGTH, UNIT_MAX_LENGTH


class Ingredient(models.Model):
    name = models.CharField("Название", max_length=NAME_MAX_LENGTH)
    measurement_unit = models.CharField(
        "Ед. измерения", max_length=UNIT_MAX_LENGTH
    )

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient"
            )
        ]
        verbose_name = "ингредиент"
        verbose_name_plural = "ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="автор",
    )
    name = models.CharField("Название", max_length=200)
    image = models.ImageField("Картинка", upload_to="recipes/")
    text = models.TextField("Описание")
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="ингредиенты",
    )
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления (мин.)",
        validators=[MinValueValidator(1)],
    )
    pub_date = models.DateTimeField("дата публикации", auto_now_add=True)

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "рецепт"
        verbose_name_plural = "рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная таблица с количеством ингредиента в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient_recipes",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = "ингредиент рецепта"
        verbose_name_plural = "ингредиенты рецептов"

        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            )
        ]

    def __str__(self):
        return (
            f"{self.ingredient.name} — {self.amount} "
            f"{self.ingredient.measurement_unit}"
        )


class UserRecipeRelation(models.Model):
    """
    Абстрактная модель: связь пользователь - рецепт
    Содержит только поля и единственный UniqueConstraint.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    recipe = models.ForeignKey("Recipe", on_delete=models.CASCADE)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_recipe"
            )
        ]


class Favorite(UserRecipeRelation):
    """Избранный рецепт"""

    class Meta(UserRecipeRelation.Meta):
        default_related_name = "favorited"
        verbose_name = "избранный рецепт"
        verbose_name_plural = "избранные рецепты"
        # переопределяем constraint, чтобы избежать дублирования имён
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user} ♥ {self.recipe}"


class ShoppingCart(UserRecipeRelation):
    # Переопределяем related_name, чтобы вернуть recipe.in_carts

    class Meta(UserRecipeRelation.Meta):
        default_related_name = "in_carts"
        verbose_name = "рецепт в списке покупок"
        verbose_name_plural = "списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart"
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.recipe}"
