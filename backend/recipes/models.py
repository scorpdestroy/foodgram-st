from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from users.models import User


class Ingredient(models.Model):
    name = models.CharField("Название", max_length=200)
    measurement_unit = models.CharField("Ед. измерения", max_length=50)

    class Meta:
        ordering = ("name",)
        unique_together = ("name", "measurement_unit")
        verbose_name = "ингредиент"
        verbose_name_plural = "ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Tag(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    color = models.CharField(
        "Цвет HEX",
        max_length=7,
        default="#49B64E",
        help_text="Напр.: #ff0000",
    )
    slug = models.SlugField("Слаг", unique=True, blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "тег"
        verbose_name_plural = "теги"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="теги",
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
    amount = models.PositiveIntegerField(
        "Количество",
        validators=[MinValueValidator(1)],
    )

    class Meta:
        unique_together = ("recipe", "ingredient")
        verbose_name = "ингредиент рецепта"
        verbose_name_plural = "ингредиенты рецептов"

    def __str__(self):
        return (
            f"{self.ingredient.name} — {self.amount} "
            f"{self.ingredient.measurement_unit}"
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorites"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorited"
    )

    class Meta:
        unique_together = ("user", "recipe")
        verbose_name = "избранный рецепт"
        verbose_name_plural = "избранные рецепты"

    def __str__(self):
        return f"{self.user} ♥ {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shopping_cart"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="in_carts"
    )

    class Meta:
        unique_together = ("user", "recipe")
        verbose_name = "рецепт в списке покупок"
        verbose_name_plural = "списки покупок"

    def __str__(self):
        return f"{self.user} → {self.recipe}"


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscriber"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscribing"
    )

    class Meta:
        unique_together = ("user", "author")
        verbose_name = "подписка"
        verbose_name_plural = "подписки"

    def __str__(self):
        return f"{self.user} ← {self.author}"
