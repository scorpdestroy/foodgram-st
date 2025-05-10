# foodgram_backend/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls", namespace="users")),
    # Djoser токены (только auth)
    path("api/auth/", include("djoser.urls.authtoken")),
    path("api/auth/", include("djoser.urls.jwt")),
    # Рецепты, теги, ингредиенты
    path("api/", include("recipes.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
