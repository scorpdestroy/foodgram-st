from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Recipe
from recipes.serializers import RecipeShortSerializer
from rest_framework import serializers
from .models import Subscription, User


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
        )
        read_only_fields = ("id", "avatar", "is_subscribed")

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=obj
        ).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="author.id")
    email = serializers.ReadOnlyField(source="author.email")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    avatar = serializers.ImageField(source="author.avatar", read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["is_subscribed"] = True
        return data

    def get_recipes(self, obj):
        """
        Короткие рецепты автора.
        Можно ограничить через ?recipes_limit=N.
        """
        request = self.context.get("request")
        qs = Recipe.objects.filter(author=obj.author).order_by("-pub_date")
        limit = request.query_params.get("recipes_limit") if request else None
        if limit is not None:
            try:
                qs = qs[: int(limit)]
            except (ValueError, TypeError):
                pass
        return RecipeShortSerializer(qs, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class SubscriptionCreateSerializer(serializers.Serializer):
    author_id = serializers.IntegerField(write_only=True)

    def validate_author_id(self, value):
        user = self.context["request"].user
        if user.id == value:
            raise serializers.ValidationError("Нельзя подписаться на себя")
        if Subscription.objects.filter(user=user, author_id=value).exists():
            raise serializers.ValidationError("Вы уже подписаны")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        author = get_object_or_404(User, pk=validated_data["author_id"])
        return Subscription.objects.create(user=user, author=author)


class SubscriptionDeleteSerializer(serializers.Serializer):
    author_id = serializers.IntegerField(write_only=True)

    def validate_author_id(self, value):
        user = self.context["request"].user
        if not Subscription.objects.filter(
            user=user, author_id=value
        ).exists():
            raise serializers.ValidationError("Вы не были подписаны")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        Subscription.objects.filter(
            user=user, author_id=self.validated_data["author_id"]
        ).delete()
