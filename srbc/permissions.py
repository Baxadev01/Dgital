from rest_framework.permissions import BasePermission


def is_authenticated(user):
    """ This function is done to upgrade to newer version of django-rest-framework
    Old version was:
        ```
        def is_authenticated(user):
            if django.VERSION < (1, 10):
                return user.is_authenticated()
            return user.is_authenticated
        ```
    """
    return user.is_authenticated


class UserCanUseDiary(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.profile.is_active
