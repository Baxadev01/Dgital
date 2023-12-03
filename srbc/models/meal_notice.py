from django.db import models

__all__ = ('MealNoticeTemplateCategory', 'MealNoticeTemplate',)


class MealNoticeTemplateCategory(models.Model):
    title = models.CharField(max_length=250)
    code = models.CharField(max_length=25, unique=True, blank=True, null=True)
    is_active = models.BooleanField(blank=True, default=True)
    scopes = models.JSONField(blank=True, default=list)

    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['code']),
        ]


class MealNoticeTemplate(models.Model):
    template = models.TextField()
    category = models.ForeignKey(
        MealNoticeTemplateCategory, related_name='templates', null=True, on_delete=models.SET_NULL
    )
    code = models.CharField(max_length=25, unique=True, blank=True, null=True)
    is_active = models.BooleanField(blank=True, default=True)
