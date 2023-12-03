from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator as SchemaGenerator, EndpointEnumerator
from drf_yasg.views import get_schema_view
# from django.contrib import admin
from rest_framework import permissions
from rest_framework.schemas import SchemaGenerator as _SchemaGenerator


class APIEndpointEnumerator(EndpointEnumerator):
    def get_allowed_methods(self, callback):
        """
        Return a list of the valid HTTP methods for this endpoint.
        """
        if hasattr(callback, 'actions'):
            actions = set(callback.actions)
            http_method_names = set(callback.cls.http_method_names)
            methods = [method.upper() for method in actions & http_method_names]
        else:
            methods = callback.cls().allowed_methods

        return [method for method in methods if method not in ('OPTIONS',)]


class DRFSchemaGenerator(_SchemaGenerator):
    default_mapping = {
        'head': 'retrieve',
        'get': 'retrieve',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }


class SwaggerSchemaGenerator(SchemaGenerator):
    endpoint_enumerator_class = APIEndpointEnumerator

    def __init__(self, info, version='', url=None, patterns=None, urlconf=None):
        super(SwaggerSchemaGenerator, self).__init__(info, version=version, url=url, patterns=patterns, urlconf=urlconf)
        self._gen = DRFSchemaGenerator(info.title, url, info.get('description', ''), patterns, urlconf)


schema_view = get_schema_view(
    openapi.Info(
        title="SRBC API",
        default_version='v1',
        terms_of_service="",
        # contact=openapi.Contact(email=""),
        # license=openapi.License(name="")
    ),
    generator_class=SwaggerSchemaGenerator,
    public=True,
    permission_classes=(permissions.AllowAny,)
)
