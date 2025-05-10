from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import Subscription
from recipes.pagination import LimitPageNumberPagination
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import User
from .serializers import (
    AvatarSerializer,
    SubscriptionCreateSerializer,
    SubscriptionDeleteSerializer,
    SubscriptionSerializer,
    UserSerializer,
)


class UserViewSet(DjoserUserViewSet):
    """
    Универсальный viewset для пользователей:
     - POST   /api/users/               → регистрация (create)
     - GET    /api/users/               → список (list) с пагинацией
     - GET    /api/users/{id}/          → детальный (retrieve)
     - GET    /api/users/me/            → свой профиль
     - POST   /api/users/{id}/subscribe → подписаться
     - DELETE /api/users/{id}/subscribe → отписаться
     - GET    /api/users/subscriptions/ → список своих подписок
     - PUT    /api/users/me/avatar/     → загрузить аватар
     - DELETE /api/users/me/avatar/     → удалить аватар
    """

    queryset = User.objects.all()
    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        if self.action in ("create", "list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=("get",), url_path="me")
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=("post", "delete"), url_path="subscribe")
    def subscribe(self, request, id=None):
        # Сначала убеждаемся, что автор существует
        author = get_object_or_404(User, pk=id)

        if request.method == "POST":
            serializer = SubscriptionCreateSerializer(
                data={"author_id": author.id}, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            sub = serializer.save()
            out = SubscriptionSerializer(sub, context={"request": request}).data
            return Response(out, status=status.HTTP_201_CREATED)

        # DELETE
        serializer = SubscriptionDeleteSerializer(
            data={"author_id": author.id}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=("get",), url_path="subscriptions")
    def subscriptions(self, request):
        qs = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(qs)
        serializer = SubscriptionSerializer(
            page or qs, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=("put", "delete"), url_path="me/avatar")
    def set_avatar(self, request):
        user = request.user
        if request.method == "PUT":
            serializer = AvatarSerializer(
                instance=user, data=request.data, context={"request": request}
            )
            # Теперь обязательность поля avatar проверяется сериализатором
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {"avatar": request.build_absolute_uri(user.avatar.url)},
                status=status.HTTP_200_OK,
            )

        # DELETE
        user.avatar.delete(save=False)
        user.avatar = None
        user.save(update_fields=["avatar"])
        return Response(status=status.HTTP_204_NO_CONTENT)
