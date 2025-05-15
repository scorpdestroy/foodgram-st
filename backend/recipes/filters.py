from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from .models import Recipe

User = get_user_model()


class NameSearchFilter(SearchFilter):
    """
    То же самое, что SearchFilter, но ищет по параметру ?name=
    """

    search_param = "name"


class RecipeFilter(filters.FilterSet):
    # вместо NumberFilter используем ModelChoiceFilter для ForeignKey
    author = filters.ModelChoiceFilter(
        field_name="author", queryset=User.objects.all()
    )
    # Boolean-фильтры из django_filters.rest_framework
    # и привязка к методам для фильтрации по текущему пользователю
    is_favorited = filters.BooleanFilter(method="filter_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = (
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def filter_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorited__user=self.request.user)
        return queryset

    def filter_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_carts__user=self.request.user)
        return queryset
