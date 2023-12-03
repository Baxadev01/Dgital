from srbc.utils.permissions import IsActiveUser

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from celery.result import AsyncResult


class CeleryTaskView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, IsActiveUser, )

    @swagger_auto_schema(
        **swagger_docs['GET /v1/tasks/{task_id}/']
    )
    def get(self, request, task_id):
        """
            Проверить статус таски
        """

        task = AsyncResult(task_id)

        if task.ready():
            if task.successful():
                # исходим из того, что респонс в нужном формате уже сформирован в таске, если все ок
                return task.result
            else:
                # если был какой-то эксепшн, то отлавливать его специально нет смысла
                # FIXME Хорошо бы разные коды ошибок делать из таски для обработки в приложениях
                return Response(
                    data={
                        "code": status.HTTP_400_BAD_REQUEST,
                        "status": "error",
                        "message": str(task.info),
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                data={
                    "status": "pending",
                }
            )
