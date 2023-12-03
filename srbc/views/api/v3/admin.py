from rest_framework.generics import ListAPIView
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from swagger_docs import swagger_docs

from srbc.serializers.general import UserShortSerializer, WaveSerializer
from srbc.models import User, Wave
from srbc.utils.permissions import HasStaffPermission


class UserPagination(PageNumberPagination):
   
   page_size = 20
   page_size_query_param = 'page_size'
   max_page_size = 1000

@method_decorator(name='get', decorator=swagger_auto_schema(
    **swagger_docs['GET /v3/staff/tools/users/']
))
class UserListAPIView(LoggingMixin, ListAPIView):
    """
        Выводит список пользователей
    """

    serializer_class = UserShortSerializer
    permission_classes = (HasStaffPermission,)
    pagination_class = UserPagination
    filter_backends=(SearchFilter, OrderingFilter)
    search_fields = ('id' ,'username', 'first_name', 'last_name')

    def get_queryset(self):
        queryset = User.objects.filter(is_staff=False)
        return queryset
    

@method_decorator(name='get', decorator=swagger_auto_schema(
    **swagger_docs['GET /v3/staff/tools/waves/']
))
class WaveListAPIView(LoggingMixin, ListAPIView):
    """
        Выводит список потоков
    """

    serializer_class = WaveSerializer
    permission_classes = (HasStaffPermission,)
    pagination_class = UserPagination
    filter_backends=(SearchFilter, OrderingFilter)
    search_fields = ("title",)

    def get_queryset(self):
        queryset = Wave.objects.filter(is_archived=False)
        return queryset