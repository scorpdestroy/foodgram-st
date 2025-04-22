import django_filters
from .models import Recipe
from rest_framework.filters import SearchFilter

class NameSearchFilter(SearchFilter):
    """
    То же самое, что SearchFilter, но ищет по параметру ?name=
    """
    search_param = 'name'

class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug'
    )
    author = django_filters.NumberFilter(field_name='author__id')
    is_favorited = django_filters.BooleanFilter(
        field_name='favorited__user', lookup_expr='exact'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='in_carts__user', lookup_expr='exact'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorited__user=self.request.user)
        return queryset

    def filter_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_carts__user=self.request.user)
        return queryset
