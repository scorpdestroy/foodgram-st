from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthor(BasePermission):
    """
    Разрешает небезопасные методы (PATCH/PUT/DELETE)
    только если request.user == recipe.author.
    """

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user
