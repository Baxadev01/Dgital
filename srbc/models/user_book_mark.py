from django.contrib.auth.models import User

from django.db import models

__all__ = ('UserBookMark',)


class UserBookMark(models.Model):
    user = models.ForeignKey(User, related_name='bookmarks', on_delete=models.CASCADE)
    bookmarked_user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
        ]
