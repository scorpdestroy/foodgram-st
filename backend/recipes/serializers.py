from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)

class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в корзину."""

    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=["user", "recipe"],
                message="Рецепт уже в корзине",
            )
        ]

    def create(self, validated_data):
        return ShoppingCart.objects.create(**validated_data)


class ShoppingCartDeleteSerializer(serializers.Serializer):
    """Сериализатор для удаления рецепта из корзины."""

    def validate(self, attrs):
        user = self.context["request"].user
        recipe = self.context["recipe"]
        try:
            attrs["instance"] = ShoppingCart.objects.get(
                user=user, recipe=recipe
            )
        except ShoppingCart.DoesNotExist:
            raise serializers.ValidationError("Рецепт не в корзине")
        return attrs

    def save(self):
        self.validated_data["instance"].delete()


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в избранное."""

    class Meta:
        model = Favorite
        fields = ("user", "recipe")
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=["user", "recipe"],
                message="Рецепт уже в избранном",
            )
        ]

    def create(self, validated_data):
        return Favorite.objects.create(**validated_data)


class FavoriteDeleteSerializer(serializers.Serializer):
    """Сериализатор для удаления рецепта из избранного."""

    def validate(self, attrs):
        user = self.context["request"].user
        recipe = self.context["recipe"]
        try:
            attrs["instance"] = Favorite.objects.get(user=user, recipe=recipe)
        except Favorite.DoesNotExist:
            raise serializers.ValidationError("Рецепт не в избранном")
        return attrs

    def save(self):
        # удаляем найденный Favorite
        self.validated_data["instance"].delete()
        return None


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")

class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта для подписок."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта для подписок."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientReadSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    ingredients_data = RecipeIngredientWriteSerializer(
        many=True, write_only=True, source="recipe_ingredients", required=False
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "ingredients_data",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
            "pub_date",
        )
        read_only_fields = (
            "id",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
            "pub_date",
        )

    def validate_image(self, value):
        if value in [None, ""]:
            raise serializers.ValidationError(
                {"image": ["Это поле обязательно."]}
            )
        return value
    
    def to_internal_value(self, data):
        data = data.copy()
        if "ingredients" in data and "ingredients_data" not in data:
            data["ingredients_data"] = data.pop("ingredients")
        return super().to_internal_value(data)

    def validate(self, attrs):
        raw = self.initial_data.get("ingredients")
        if raw is None:
            raise serializers.ValidationError(
                {"ingredients": ["Это поле обязательно."]}
            )
        if not isinstance(raw, list) or len(raw) == 0:
            raise serializers.ValidationError(
                {"ingredients": ["Добавьте хотя бы один ингредиент."]}
            )
        seen = set()
        for ing in raw:
            iid = ing.get("id")
            if iid in seen:
                raise serializers.ValidationError(
                    {"ingredients": ["Ингредиенты должны быть уникальными."]}
                )
            seen.add(iid)
            amt = ing.get("amount")
            if amt is None or int(amt) < 1:
                raise serializers.ValidationError(
                    {"ingredients": ["Количество должно быть ≥ 1."]}
                )
        ct = attrs.get("cooking_time")
        if ct is None or ct < 1:
            raise serializers.ValidationError(
                {"cooking_time": ["Время приготовления должно быть ≥ 1."]}
            )
        return attrs

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.favorited.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.in_carts.filter(user=user).exists()

    def _create_ingredients(self, recipe, ingredients):
        objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ing["ingredient"],
                amount=ing["amount"],
            )
            for ing in ingredients
        ]
        RecipeIngredient.objects.bulk_create(objs)

    def create(self, validated_data):
        ingredients = validated_data.pop("recipe_ingredients", [])
        # Привязываем текущего пользователя как автора
        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data
        )
        self._create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        if "recipe_ingredients" in validated_data:
            instance.recipe_ingredients.all().delete()
            self._create_ingredients(
                instance, validated_data.pop("recipe_ingredients")
            )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        from users.serializers import UserSerializer

        # только автор остаётся «как есть»
        rep["author"] = UserSerializer(
            instance.author, context=self.context
        ).data
        if rep.get("image") is None:
            rep["image"] = ""
        # удаляем из вывода поля, которых нет в responseSchema
        rep.pop("tags", None)
        rep.pop("pub_date", None)
        return rep
