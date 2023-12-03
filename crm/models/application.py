from datetime import date
from django.conf import settings
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_countries.fields import CountryField

from .campaign import Campaign
from .payments import Payment

from srbc.models.tariff import Tariff
from srbc.models.user_note import UserNote

from shared.models import DecimalRangeField

__all__ = ('Application',)


class Application(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='application')
    campaign = models.ForeignKey(Campaign, blank=True, null=True, on_delete=models.SET_NULL)
    gender = models.CharField(
        max_length=1,
        choices=(('M', _("Мужской")),
                 ('F', _("Женский"))),
        default='F',
        verbose_name="Пол"
    )

    tariff = models.ForeignKey(Tariff, blank=True, null=True, on_delete=models.SET_NULL)

    is_payment_allowed = models.BooleanField(blank=True, default=False, verbose_name="Разрешена оплата")
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    email = models.EmailField(verbose_name="Электронная почта")
    email_status = models.CharField(
        max_length=25,
        choices=(
            ('NEW', "Новый"),
            ('PENDING', "Ожидает подтверждения"),
            ('APPROVED', "Подтвержден"),
            ('DISCONNECTED', "Отписан"),
        ),
        blank=True,
        default='NEW'
    )
    phone = models.CharField(max_length=100, verbose_name="Номер мобильного телефона", blank=True, null=True)
    baby_case = models.CharField(max_length=100, verbose_name="Особый случай", default='NONE', choices=(
        ('PREGNANT', "Беременность"),
        ('FEEDING', "Кормление грудью"),
        ('NONE', "Ничего из перечисленного"),
    ))
    baby_birthdate = models.DateField(blank=True, null=True, verbose_name="Дата рождения ребёнка")
    country_old = models.CharField(max_length=100, verbose_name="Страна", null=True)
    country = CountryField(verbose_name="Страна")
    city = models.CharField(max_length=100, verbose_name="Город", null=True)
    height = models.IntegerField(verbose_name="Ваш рост, в см", null=True)
    weight = DecimalRangeField(decimal_places=3, max_digits=8, max_value=500, min_value=1,
                               verbose_name="Ваш текущий (стартовый) вес, в кг", null=True)

    age = models.IntegerField(verbose_name="Ваш возраст", blank=True, null=True)
    birth_year = models.IntegerField(verbose_name="Год рождения", null=True)
    sickness = models.TextField(verbose_name="Имеющиеся заболевания", null=True)
    goal_weight = DecimalRangeField(decimal_places=3, max_digits=8, max_value=500, min_value=30,
                                    verbose_name="Целевой вес", null=True)
    goals = models.TextField(verbose_name="Цели на проекте", null=True)
    need_tracker = models.BooleanField(default=False, blank=True, verbose_name="Хочу фитнесс-трекер")
    is_approved = models.BooleanField(default=False, blank=True, verbose_name="Анкета проверена")
    social_acc_status = models.CharField(
        max_length=25,
        choices=(
            ('PENDING', "Ожидает подтверждения"),
            ('APPROVED', "Подтвержден"),
            ('SUSPICIOUS', "Подозрительный"),
            ('REJECTED', "Отклонён"),
        ),
        blank=True,
        default='PENDING'
    )

    admission_status = models.CharField(
        max_length=100, blank=True,
        choices=(
            ('NOT_STARTED', _("Не дошел")),
            ('IN_PROGRESS', _("В процессе")),
            ('DONE', _("Завершил")),
            ('PASSED', _("Проверено, всё ок")),
            ('FAILED', _("Проверено, завалил")),
            ('REJECTED', _("Отказано")),
            ('ACCEPTED', _("Принят")),
        ),
        default='NOT_STARTED'
    )

    active_payment_order = models.ForeignKey(Payment, blank=True, null=True, on_delete=models.SET_NULL)
    tos_signed_date = models.DateTimeField(blank=True, null=True)
    is_payment_special = models.BooleanField(blank=True, default=False, verbose_name="Особые условия оплаты")

    @property
    def imt(self):
        if not self.weight:
            return None

        if not self.height:
            return None

        return Decimal(10000) * self.weight / (Decimal(self.height) * Decimal(self.height))

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self.is_already_approved = self.is_approved

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.is_already_approved and self.is_approved:
            self.is_already_approved = True
            if self.sickness and len(self.sickness) > 1 and self.sickness.lower() not in ["нет", "отсутствуют"]:
                if self.user.profile.wave:
                    added_date = self.user.profile.wave.start_date
                else:
                    added_date = date.today()

                note_text = 'Имеющиеся заболевания:\n%s' % self.sickness
                # Dirty Hack: author_id hardcoded.
                sickness_note = UserNote(
                    user=self.user,
                    date_added=added_date,
                    label='NB',
                    is_published=False,
                    content=note_text,
                    author_id=settings.SYSTEM_USER_ID
                )
                sickness_note.save()

        super(Application, self).save(force_insert, force_update)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['need_tracker']),
            models.Index(fields=['is_approved']),
        ]
