import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import (
    Ingredient, Tag, Recipe, RecipeIngredient
)


class Base64ImageField(serializers.ImageField):
    """
    Принимает строку вида "data:image/png;base64,AAA..." и
    преобразует её в файл.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, imgstr = data.split(';base64,')
            ext = header.split('/')[-1]
            file_name = f'{uuid.uuid4().hex[:10]}.{ext}'
            data = ContentFile(base64.b64decode(imgstr), name=file_name)
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта для подписок."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    ingredients_data = RecipeIngredientWriteSerializer(
        many=True,
        write_only=True,
        source='recipe_ingredients',
        required=False
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'tags',
            'ingredients', 'ingredients_data',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time', 'pub_date'
        )
        read_only_fields = (
            'id', 'author', 'is_favorited',
            'is_in_shopping_cart', 'pub_date'
        )

    def to_internal_value(self, data):
        data = data.copy()
        if 'ingredients' in data and 'ingredients_data' not in data:
            data['ingredients_data'] = data.pop('ingredients')
        return super().to_internal_value(data)

    def validate(self, attrs):
        raw = self.initial_data.get('ingredients')
        if raw is None:
            raise serializers.ValidationError({
                'ingredients': ['Это поле обязательно.']
            })
        if not isinstance(raw, list) or len(raw) == 0:
            raise serializers.ValidationError({
                'ingredients': ['Добавьте хотя бы один ингредиент.']
            })
        seen = set()
        for ing in raw:
            iid = ing.get('id')
            if iid in seen:
                raise serializers.ValidationError({
                    'ingredients': ['Ингредиенты должны быть уникальными.']
                })
            seen.add(iid)
            amt = ing.get('amount')
            if amt is None or int(amt) < 1:
                raise serializers.ValidationError({
                    'ingredients': ['Количество должно быть ≥ 1.']
                })
        ct = attrs.get('cooking_time')
        if ct is None or ct < 1:
            raise serializers.ValidationError({
                'cooking_time': ['Время приготовления должно быть ≥ 1.']
            })
        return attrs

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.favorited.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.in_carts.filter(user=user).exists()

    def _create_ingredients(self, recipe, ingredients):
        objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ing['ingredient'],
                amount=ing['amount']
            )
            for ing in ingredients
        ]
        RecipeIngredient.objects.bulk_create(objs)

    def create(self, validated_data):
        ingredients = validated_data.pop('recipe_ingredients', [])
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            instance.tags.set(validated_data.pop('tags'))
        if 'recipe_ingredients' in validated_data:
            instance.recipe_ingredients.all().delete()
            self._create_ingredients(
                instance,
                validated_data.pop('recipe_ingredients')
            )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        from users.serializers import UserSerializer
        # только автор остаётся «как есть»
        rep['author'] = UserSerializer(
            instance.author,
            context=self.context
        ).data
        # удаляем из вывода поля, которых нет в responseSchema
        rep.pop('tags', None)
        rep.pop('pub_date', None)
        return rep
    
