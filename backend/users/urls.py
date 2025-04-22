# users/urls.py

from django.urls import path
from djoser.views import UserViewSet as DjoserUserViewSet
from .views import UserViewSet

app_name = 'users'

urlpatterns = [
    # 1) Сброс/смена пароля (Djoser)
    #    POST /api/users/set_password/
    path(
        'set_password/',
        DjoserUserViewSet.as_view({'post': 'set_password'}),
        name='user-set-password'
    ),

    # 2) Регистрация + список (GET/POST на одном и том же пути)
    #    GET  /api/users/
    #    POST /api/users/
    path(
        '',
        UserViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='user-list'
    ),

    # 3) Детали конкретного пользователя
    #    GET /api/users/{pk}/
    path(
        '<int:pk>/',
        UserViewSet.as_view({'get': 'retrieve'}),
        name='user-detail'
    ),

    # 4) Мой профиль
    #    GET /api/users/me/
    path(
        'me/',
        UserViewSet.as_view({'get': 'me'}),
        name='user-me'
    ),

    # 5) Подписка / отписка на автора
    #    POST   /api/users/{pk}/subscribe/
    #    DELETE /api/users/{pk}/subscribe/
    path(
        '<int:pk>/subscribe/',
        UserViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}),
        name='user-subscribe'
    ),

    # 6) Мои подписки
    #    GET /api/users/subscriptions/
    path(
        'subscriptions/',
        UserViewSet.as_view({'get': 'subscriptions'}),
        name='user-subscriptions'
    ),

    # 7) Загрузка/удаление аватара
    #    PUT    /api/users/me/avatar/
    #    DELETE /api/users/me/avatar/
    path(
        'me/avatar/',
        UserViewSet.as_view({'put': 'set_avatar', 'delete': 'set_avatar'}),
        name='user-avatar'
    ),
]
