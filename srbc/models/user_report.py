import binascii
import hashlib
import os
from uuid import uuid4

from django.contrib.auth.models import User
from django.db import models

__all__ = ('UserReport', 'user_report_hashid', 'report_chart_upload_to', 'report_pdf_upload_to',)


def user_report_hashid():
    hashid = hashlib.pbkdf2_hmac('sha256', uuid4().hex.encode(), uuid4().hex.encode(), 100)
    return binascii.hexlify(hashid).decode()


def report_pdf_upload_to(instance, filename):
    return os.path.join(
        'reports',
        instance.date.strftime('%Y-%m-%d'),
        "%s.pdf" % instance.hashid
    )


def report_chart_upload_to(instance, filename):
    return os.path.join(
        'reports_assets',
        '%s' % instance.user_id,
        instance.date.strftime('%Y-%m-%d'),
        "%s.png" % instance.hashid
    )


class UserReport(models.Model):
    hashid = models.CharField(max_length=64, default=user_report_hashid, unique=True)
    user = models.ForeignKey(User, related_name="reports", on_delete=models.CASCADE)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    weight_start = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4)
    weight_current = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4)
    bmi_start = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4)
    bmi_current = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4)
    weight_delta_weekly = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4)
    weight_delta_weekly_mon = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4)
    days_passed = models.IntegerField(blank=True, null=True)
    meals_present = models.IntegerField(blank=True, null=True)
    meals_relevance = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4)
    meal_faults = models.JSONField(blank=True, null=True)
    steps_fulfilled = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4)
    sleep_fulfilled = models.DecimalField(blank=True, null=True, decimal_places=1, max_digits=4)
    overcalories_count = models.IntegerField(blank=True, null=True)
    chart_data = models.JSONField(blank=True, null=True)
    chart_image = models.ImageField(blank=True, null=True, upload_to=report_chart_upload_to)
    pdf_file = models.FileField(blank=True, null=True, upload_to=report_pdf_upload_to)

# INSERT INTO srbc_mealproduct ( title, component_type, is_verified, "language" ) (
# SELECT DISTINCT ON (LOWER ( description ))
#   LOWER ( description ),
# 	component_type,
# 	FALSE,
# 	'ru'
# FROM
# 	srbc_mealcomponent mc
# WHERE
# 	NOT EXISTS ( SELECT title FROM srbc_mealproduct mp WHERE LOWER ( mc.description ) = mp.title )
# 	);
