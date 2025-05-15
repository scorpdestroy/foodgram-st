from rest_framework.pagination import PageNumberPagination
from .constants import PAGE_SIZE


class LimitPageNumberPagination(PageNumberPagination):
    # по умолчанию возвращаем по 10 элементов на страницу
    page_size = PAGE_SIZE
    # позволяем клиенту менять размер через параметр ?limit=
    page_size_query_param = "limit"
