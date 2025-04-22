from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer

import re
from .models import User
from recipes.models import Subscription, Recipe
from recipes.serializers import Base64ImageField  # импорт только Base64ImageField


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

class UserSerializer(DjoserUserSerializer):
    avatar = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'avatar', 'is_subscribed',
        )
        read_only_fields = ('id', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()

    def get_avatar(self, obj):
        """
        Возвращает полный URL аватара или пустую строку,
        если аватар не установлен.
        """
        request = self.context.get('request')
        if not obj.avatar:
            return ""
        return request.build_absolute_uri(obj.avatar.url)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта для подписок."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    avatar = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'avatar', 'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_avatar(self, obj):
        # Берём аватар автора, а не подписки
        author = obj.author
        if not author.avatar:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(author.avatar.url)


    def get_is_subscribed(self, obj):
        # в контексте подписки всегда True
        return True

    def get_recipes(self, obj):
        """
        Короткие рецепты автора.
        Можно ограничить через ?recipes_limit=N.
        """
        request = self.context.get('request')
        qs = Recipe.objects.filter(author=obj.author).order_by('-pub_date')
        limit = request.query_params.get('recipes_limit') if request else None
        if limit is not None:
            try:
                qs = qs[:int(limit)]
            except (ValueError, TypeError):
                pass
        return RecipeShortSerializer(qs, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()
    
class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')

class CustomUserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        # разрешаем только буквы, цифры, подчёркивание, точку, @, +, -
        if not re.fullmatch(r'^[\w.@+-]+$', value):
            raise serializers.ValidationError(
                'Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_'
            )
        return value

    def create(self, validated_data):
        User = get_user_model()
        return User.objects.create_user(**validated_data)

    def to_representation(self, instance):
        return SimpleUserSerializer(instance, context=self.context).data