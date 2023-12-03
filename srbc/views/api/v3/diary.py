from rest_framework.generics import ListAPIView
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from django.utils import timezone

from swagger_docs import swagger_docs
from srbc.serializers.general import UserReportSerializer
from srbc.models import UserReport

class UserReportPagination(PageNumberPagination):
   
   page_size = 5
   page_size_query_param = 'page_size'
   max_page_size = 1000


@method_decorator(name='get', decorator=swagger_auto_schema(
    filter_inspectors=[UserReportPagination],
    **swagger_docs['GET /v3/diary/reports/']
))
class UserReportListAPIView(LoggingMixin, ListAPIView):
    """
        Выводит список отчетов пользователя
    """

    serializer_class = UserReportSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = UserReportPagination

    def get_queryset(self):
        queryset = UserReport.objects.filter(user=self.request.user).order_by('-date')
        return queryset

