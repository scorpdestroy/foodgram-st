from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthor(BasePermission):
    """
    Разрешает небезопасные методы (PATCH/PUT/DELETE)
    только если request.user == recipe.author.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
