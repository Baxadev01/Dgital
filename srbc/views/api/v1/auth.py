import io
import qrcode
import base64

from django.conf import settings

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from srbc.utils.auth import get_short_time_jwt


class JwtTemporaryToken(LoggingMixin, APIView):
    permission_classes = (IsAuthenticated,)

    @swagger_auto_schema(
        **swagger_docs['GET /v1/auth/temporary/']
    )
    def get(self, request):
        """
            Получение jwt токена, который действует 5 минут
        """
        return Response({
            "token": get_short_time_jwt(request.user)
        })
