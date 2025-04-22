from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from .filters import NameSearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import RecipeShortSerializer

from .models import (
    Ingredient, Tag, Recipe, RecipeIngredient,
    Favorite, ShoppingCart
)
from .serializers import (
    IngredientSerializer, TagSerializer,
    RecipeSerializer
)
from .filters import RecipeFilter


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)  # поиск по началу названия
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class RecipeViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        qs = Recipe.objects.all().order_by('-pub_date')
        user = self.request.user
        params = self.request.query_params
        # фильтрация по корзине
        if user.is_authenticated:
            val = params.get('is_in_shopping_cart')
            if val in ('1', 'true', 'True'):
                qs = qs.filter(in_carts__user=user)
            # фильтрация по избранному
            val = params.get('is_favorited')
            if val in ('1', 'true', 'True'):
                qs = qs.filter(favorited__user=user)
        return qs
    
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter  
    class IsAuthor(BasePermission):
        """
        Разрешает небезопасные методы (PATCH/PUT/DELETE) 
        только если request.user == recipe.author.
        """
        def has_object_permission(self, request, view, obj):
            # SAFE_METHODS (GET, HEAD, OPTIONS) всегда можно
            if request.method in ('GET', 'HEAD', 'OPTIONS'):
                return True
            return obj.author == request.user

    def get_permissions(self):
        # создание — любой залогиненный
        if self.action == 'create':
            return [IsAuthenticated()]
        # редактирование или удаление — только автор
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), self.IsAuthor()]
        # избранное и корзина — любой залогиненный
        if self.action in ('favorite', 'shopping_cart'):
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def get_link(self, request, pk=None):
        """
        Возвращает короткую постоянную ссылку на рецепт.
        Поле ответа называется "short-link".
        """
        recipe = self.get_object()
        link = request.build_absolute_uri(
            reverse('recipe-detail', args=[recipe.id])
        )
        return Response(
            {'short-link': link},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            obj, created = Favorite.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # возвращаем короткий сериализованный рецепт
            data = RecipeShortSerializer(
                recipe, context={'request': request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        # DELETE
        deleted, _ = Favorite.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепт не в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            obj, created = ShoppingCart.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': 'Рецепт уже в корзине'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = RecipeShortSerializer(
                recipe, context={'request': request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        # DELETE
        deleted, _ = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепт не в корзине'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        qs = RecipeIngredient.objects.filter(
            recipe__in_carts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total=Sum('amount'))
        lines = [
            f"{item['ingredient__name']} ({item['ingredient__measurement_unit']}) — {item['total']}"
            for item in qs
        ]
        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response
