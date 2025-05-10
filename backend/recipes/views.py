from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, BasePermission,
                                        IsAuthenticated)
from rest_framework.response import Response

from .filters import NameSearchFilter, RecipeFilter
from .models import Ingredient, Recipe, RecipeIngredient
from .serializers import (FavoriteDeleteSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeSerializer,
                          RecipeShortSerializer, ShoppingCartDeleteSerializer,
                          ShoppingCartSerializer)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API-endpoint для просмотра ингредиентов.

    Поиск по началу названия выполняется кастомным фильтром `NameSearchFilter`,
    поэтому дополнительный `search_fields` не нужен.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = (NameSearchFilter,)  # поиск по началу названия
    pagination_class = None


class IsAuthor(BasePermission):
    """
    Разрешает небезопасные методы (PATCH/PUT/DELETE)
    только если request.user == recipe.author.
    """

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS (GET, HEAD, OPTIONS) всегда можно
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return obj.author == request.user


class RecipeViewSet(viewsets.ModelViewSet):

    queryset = Recipe.objects.all().order_by("-pub_date")
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        # создание, избранное и корзина — любой залогиненный
        if self.action in ("create", "favorite", "shopping_cart"):
            return [IsAuthenticated()]
        # редактирование или удаление — только автор
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAuthor()]
        # остальное — открытое
        return [AllowAny()]

    @action(
        detail=True,
        methods=("get",),
        url_path="get-link",
        permission_classes=(AllowAny,),
    )
    def get_link(self, request, pk=None):
        """
        Возвращает короткую постоянную ссылку на рецепт.
        Поле ответа называется "short-link".
        """
        recipe = self.get_object()
        link = request.build_absolute_uri(reverse("recipe-detail", args=[recipe.id]))
        return Response({"short-link": link}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            serializer = FavoriteSerializer(
                data={"user": user.id, "recipe": recipe.id},
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = RecipeShortSerializer(recipe, context={"request": request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        # DELETE
        serializer = FavoriteDeleteSerializer(
            data={}, context={"request": request, "recipe": recipe}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            serializer = ShoppingCartSerializer(
                data={"user": user.id, "recipe": recipe.id},
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = RecipeShortSerializer(recipe, context={"request": request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        # DELETE
        serializer = ShoppingCartDeleteSerializer(
            data={}, context={"request": request, "recipe": recipe}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=("get",), permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        qs = (
            RecipeIngredient.objects.filter(recipe__in_carts__user=user)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total=Sum("amount"))
        )
        lines = [
            (
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total']}"
            )
            for item in qs
        ]
        content = "\n".join(lines)
        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'
        return response
