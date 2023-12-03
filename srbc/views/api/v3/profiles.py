from rest_framework.generics import ListAPIView
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from django.utils import timezone

from swagger_docs import swagger_docs
from srbc.serializers.general import UserNoteSerializer
from srbc.models import UserNote

class UserNotePagination(PageNumberPagination):
   
   page_size = 24
   page_size_query_param = 'page_size'
   max_page_size = 1000

@method_decorator(name='get', decorator=swagger_auto_schema(
    filter_inspectors=[UserNotePagination],
    **swagger_docs['GET /v3/profiles/usernote/']
))
class UserNoteListAPIView(LoggingMixin, ListAPIView):
    """
        Выводит список персональных рекомендаций
    """

    serializer_class = UserNoteSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = UserNotePagination

    def get_queryset(self):
      
        queryset = UserNote.objects \
                .filter(user=self.request.user, is_published=True, date_added__lte=timezone.now()) \
                .exclude(label__in=['DOC', ]) \
                .order_by("-date_added")

        return queryset