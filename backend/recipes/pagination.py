from rest_framework.pagination import PageNumberPagination

class LimitPageNumberPagination(PageNumberPagination):
    # по умолчанию возвращаем по 10 элементов на страницу
    page_size = 10
    # позволяем клиенту менять размер через параметр ?limit=
    page_size_query_param = 'limit'
