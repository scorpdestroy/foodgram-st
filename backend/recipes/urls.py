from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet

router = DefaultRouter()
# Убрана необязательная r-строка, так как здесь нет escape-последовательностей
router.register("ingredients", IngredientViewSet, basename="ingredient")
router.register("recipes", RecipeViewSet, basename="recipe")

urlpatterns = router.urls
