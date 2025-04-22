from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Subscription, Recipe
from recipes.serializers import Base64ImageField
from recipes.pagination import LimitPageNumberPagination

from .models import User
from .serializers import (
    UserSerializer,
    CustomUserCreateSerializer,
    SubscriptionSerializer,
    AvatarSerializer,
    RecipeShortSerializer
)


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    Универсальный viewset для пользователей:
     - POST   /api/users/               → регистрация (create)
     - GET    /api/users/               → список (list) с пагинацией
     - GET    /api/users/{pk}/          → детальный (retrieve)
     - GET    /api/users/me/            → свой профиль
     - POST   /api/users/{pk}/subscribe → подписаться
     - DELETE /api/users/{pk}/subscribe → отписаться
     - GET    /api/users/subscriptions/ → список своих подписок
     - PUT    /api/users/me/avatar/     → загрузить аватар
     - DELETE /api/users/me/avatar/     → удалить аватар
    """
    queryset = User.objects.all()
    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        if self.action in ('create', 'list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=('get',), url_path='me')
    def me(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=('post', 'delete'), url_path='subscribe')
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)
    
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            sub, created = Subscription.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscriptionSerializer(
                sub, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
        # DELETE
        deleted, _ = Subscription.objects.filter(
            user=user, author=author
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не были подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=False, methods=('get',), url_path='subscriptions')
    def subscriptions(self, request):
        qs = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(qs)
        serializer = SubscriptionSerializer(
            page or qs, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=('put', 'delete'), url_path='me/avatar')
    def set_avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            if not request.data.get('avatar'):
                return Response(
                    {'avatar': ['Это поле обязательно.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = AvatarSerializer(
                instance=user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK
            )
        # DELETE
        user.avatar.delete(save=False)
        user.avatar = None
        user.save(update_fields=['avatar'])
        return Response(status=status.HTTP_204_NO_CONTENT)
