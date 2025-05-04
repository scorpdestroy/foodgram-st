from django.urls import path
from rest_framework.routers import DefaultRouter
from djoser.views import UserViewSet as DjoserUserViewSet

from .views import UserViewSet

app_name = 'users'

# --- 1. Роутер для всех методов вашего UserViewSet -------------------------
router = DefaultRouter()
# регистрируем на пустом префиксе:
#   /api/users/               (list, create)
#   /api/users/{pk}/          (retrieve)
#   /api/users/me/            (action)
#   /api/users/{pk}/subscribe/  (action)
#   /api/users/subscriptions/   (action)
#   /api/users/me/avatar/       (action)
router.register(r'', UserViewSet, basename='user')

# --- 2. Отдельный путь для смены пароля (обрабатывает Djoser потому что что-то не так) --------------
urlpatterns = [
    path(
        'set_password/',
        DjoserUserViewSet.as_view({'post': 'set_password'}),
        name='user-set-password',
    ),
]

# --- 3. Добавляем все сгенерированные URL роутера --------------------------
urlpatterns += router.urls
