from datetime import date, timedelta

from django.conf import settings
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models import Q
from django.db.models.signals import post_save
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from crm.models.payments import Payment
from crm.models.tariff_history import TariffHistory
from shared.models import ChoiceArrayField, DecimalRangeField
from srbc.utils.timezones import PRETTY_TIMEZONE_CHOICES
from .stat_group_history import StatGroupHistory
from .subscription import Subscription
from .tariff import Tariff
from .wave import Wave
from .tariff_group import TariffGroup

__all__ = ('Profile',)


class Profile(models.Model):
    STAT_GROUPS = {
        'INCLUDE_MAIN': {
            "to_meal": True,
            "to_analyze": True,
            "to_renew": True,
        },
        'INCLUDE_GENERAL': {
            "to_meal": True,
            "to_analyze": True,
            "to_renew": True,
        },
        'INCLUDE_BASELINE': {
            "to_meal": True,
            "to_analyze": False,
            "to_renew": True,
        },
        'EXCLUDE_REQUESTED': {
            "to_meal": False,
            "to_analyze": False,
            "to_renew": False,
        },
        'EXCLUDE_REQUESTED_TMP': {
            "to_meal": False,
            "to_analyze": False,
            "to_renew": True,

        },
        'EXCLUDE_FORCED': {
            "to_meal": False,
            "to_analyze": False,
            "to_renew": False,
        },
        'EXCLUDE_FORCED_REANIMATED': {
            "to_meal": True,
            "to_analyze": False,
            "to_renew": True,
        },
    }

    MEAL_ANALYZE_MODE_AUTO = 0
    MEAL_ANALYZE_MODE_FULL_TEXT = 1
    MEAL_ANALYZE_MODE_SHORT_TEXT = 2
    MEAL_ANALYZE_MODE_NO_TEXT = 3

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            # models.Index(fields=['wave']),
            models.Index(fields=['group_leader']),
            # models.Index(fields=['is_active']),
            # models.Index(fields=['is_in_club']),
            models.Index(fields=['stat_group']),
            models.Index(fields=['meal_analyze_mode']),
            models.Index(fields=['is_meal_analyze_mode_locked']),
        ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    username_is_editable = models.BooleanField(blank=True, default=True)
    deleted_wave = models.ForeignKey(Wave, blank=True, null=True, on_delete=models.SET_NULL)

    deleted_tariff = models.ForeignKey(
        Tariff, blank=True, null=True, related_name='participants', on_delete=models.SET_NULL
    )

    tariff_next = models.ForeignKey(
        Tariff, blank=True, null=True, related_name='participants_next', on_delete=models.SET_NULL
    )
    tariff_valid_from = models.DateField(blank=True, null=True)
    tariff_valid_until = models.DateField(blank=True, null=True)

    deleted_valid_until = models.DateField(blank=True, null=True)

    meal_days_allowed_delay = models.SmallIntegerField(blank=True, null=False, default=2,
                                                       verbose_name="Допустимая задержка внесения рационов (дней)")

    gender = models.CharField(
        max_length=1,
        choices=(('M', _("Мужской")),
                 ('F', _("Женский"))),
        default='F'
    )

    group_leader = models.ForeignKey(
        User,
        related_name='squadron',
        limit_choices_to={'groups__name': "TeamLead"},
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    deleted_is_active = models.BooleanField(default=False, blank=True, verbose_name="Профиль активен")
    deletedis_in_club = models.BooleanField(default=False, blank=True, verbose_name="В клубе")
    # is_self_meal_formula = models.BooleanField(default=False, blank=True, verbose_name=u"Cамооцифровка")
    is_perfect_weight = models.BooleanField(default=False, blank=True, verbose_name="Идеальный вес")
    is_meal_comments_allowed = models.BooleanField(default=True, blank=True,
                                                   verbose_name="Разрешены комментарии к рациону")
    meals_sergeant = models.ForeignKey(User, related_name="meal_users",
                                       null=True, blank=True, on_delete=models.SET_NULL,
                                       limit_choices_to={'groups__name__in': ["TeamLead", "Sergeant", "RapidCat"]})

    meal_analyze_mode = models.SmallIntegerField(
        blank=True, default=1, choices=(
            (0, "Автооцифровка"),
            (1, "Подробные комментарии"),
            (2, "Краткие комментарии"),
            (3, "Без комментариев"),
        )
    )
    is_meal_analyze_mode_locked = models.BooleanField(blank=True, default=False)

    mobile_number = models.CharField(max_length=100, blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    is_instagram_private = models.BooleanField(default=False, blank=True, verbose_name="Закрытый инстаграм")
    is_pregnant_old = models.BooleanField(default=False, blank=True, verbose_name="Беременная/Кормящая")

    goal_weight = DecimalRangeField(
        decimal_places=3, max_digits=8, max_value=500, min_value=30,
        verbose_name="Целевой вес", null=True, blank=True
    )
    display_goal_weight = models.BooleanField(blank=True, default=True)

    baby_case = models.CharField(max_length=100, verbose_name="Особый случай", default='NONE', choices=(
        ('PREGNANT', "Беременность"),
        ('FEEDING', "Кормление грудью"),
        ('NONE', "Ничего из перечисленного"),
    ))
    baby_birthdate = models.DateField(blank=True, null=True, verbose_name="Дата родов")

    warning_flag = models.CharField(
        max_length=20,
        choices=(('TEST', _("Необходимо специализированное обследование")),
                 ('OBSERVATION', _("Имеются особенности обмена, требуется наблюдение")),
                 ('TREATMENT', _("Под наблюдением врачей")),
                 ('DANGER', _("Необходимо лечение, требуется посещение врача")),
                 ('PR', _("Необходимо постоянное следование персональным рекомендациям")),
                 ('OOC', _("Питание не соответствует методичке и общим рекомендациям проекта")),
                 ('OK', _("Всё ок"))),
        default='OK'
    )

    tracker_brand = models.CharField(
        max_length=100, default='OTHER',
        choices=(
            ('XIAOMI', "Xiaomi"),
            ('JAWBONE', "Jawbone"),
            ('OTHER', "Другой"),
        )
    )

    __stat_group_orig = None
    __tariff_next_orig = None

    stat_group = models.CharField(
        max_length=30,
        choices=(
            ('INCLUDE_MAIN', 'INCLUDE_MAIN',),
            ('INCLUDE_GENERAL', 'INCLUDE_GENERAL',),
            ('INCLUDE_BASELINE', 'INCLUDE_BASELINE',),
            ('EXCLUDE_REQUESTED', 'EXCLUDE_REQUESTED',),
            ('EXCLUDE_REQUESTED_TMP', 'EXCLUDE_REQUESTED_TMP',),
            ('EXCLUDE_FORCED', 'EXCLUDE_FORCED',),
            ('EXCLUDE_FORCED_REANIMATED', 'EXCLUDE_FORCED_REANIMATED',),
        ),
        default='INCLUDE_GENERAL'
    )
    away_until = models.DateField(blank=True, null=True)

    treatment = models.TextField(blank=True, default='')
    mifit_id = models.CharField(max_length=20, blank=True, null=True)
    mifit_last_sync = models.DateTimeField(blank=True, null=True)
    telegram_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    # telegram_join_code = models.CharField(max_length=100, null=True, blank=True)
    telegram_first_name = models.CharField(max_length=100, null=True, blank=True)
    telegram_last_name = models.CharField(max_length=100, null=True, blank=True)
    # telegram_is_in_channel = models.BooleanField(blank=True, default=False)

    instagram_link_code = models.CharField(max_length=100, null=True, blank=True)
    trueweight_id = models.CharField(max_length=11, blank=True, null=True)

    deleted_communication_mode = models.CharField(
        max_length=20, blank=True, null=True,
        choices=(
            ('CHANNEL', "Канал"),
            ('CHAT', "Чат"),
        )
    )

    timezone = models.CharField(max_length=255, choices=PRETTY_TIMEZONE_CHOICES, blank=True, null=True,
                                default='Europe/Moscow')
    height = models.IntegerField(blank=True, null=True)
    birth_year = models.IntegerField(blank=True, null=True)
    visibility = models.CharField(
        max_length=20,
        choices=(
            ('PUBLIC', "Открытый"),
            ('RESTRICTED', "Ограниченный"),
            ('PRIVATE', "Закрытый"),
        ),
        default='PRIVATE'
    )

    agreement_signed_date = models.DateTimeField(blank=True, null=True)
    instagram_update_required = models.BooleanField(blank=True, default=False)

    widgets_display = ChoiceArrayField(models.CharField(
        max_length=50,
        choices=(
            ('NOTES', "Персональные рекомендации"),
            ('CALENDAR', "Календарь данных"),
            ('MEETINGS', "Последние митинги"),
            ('ALARM', "Алярм"),
            ('CHARTS', "Графики с данными"),
        )
    ), blank=True, default=list)

    active_tariff_history = models.ForeignKey(TariffHistory, blank=True, null=True, on_delete=models.SET_NULL)
    next_tariff_history = models.ForeignKey(
        TariffHistory, related_name="profile_next", blank=True, null=True, on_delete=models.SET_NULL)

    has_desktop_access = models.BooleanField(blank=True, default=True)

    def has_permission(self, permission_code, quota_used=None):
        return False

    @property
    def is_self_meal_formula(self):
        return self.meal_analyze_mode == Profile.MEAL_ANALYZE_MODE_AUTO

    @property
    def is_pregnant(self):
        return self.baby_case != 'NONE'

    @property
    def is_blocked(self):
        return not self.user.is_active

    @cached_property
    def available_widgets(self):
        widgets = []
        if not self.tariff or not self.tariff.tariff_group:
            return widgets

        tariff_group = self.tariff.tariff_group

        if tariff_group.expertise_access:
            widgets.extend(['ALARM', 'NOTES'])

        if tariff_group.diary_access != tariff_group.DIARY_ACCESS_READ:
            widgets.extend(['CALENDAR', 'CHARTS'])

        if tariff_group.meetings_access != tariff_group.MEETINGS_NO_ACCESS:
            widgets.append('MEETINGS')

        return widgets

    @cached_property
    def tariff(self):
        if not self.active_tariff_history:
            # если есть оплаченная запись в будущем, то несмотря на текущую неактивность
            # возвращаем базовый тариф
            if self.next_tariff_history:
                return Tariff.objects.get(slug=settings.BASE_TARIFF)

            return None

        return self.active_tariff_history.tariff

    @cached_property
    def wave(self):
        if self.active_tariff_history and self.active_tariff_history.wave_id:
            return self.active_tariff_history.wave

        # чтобы не вызывать несколько раз
        last_record = self.last_active_tariff_history_record

        if last_record and last_record.wave_id:
            return last_record.wave

        return None

    @cached_property
    def has_wave_tariff_history(self):
        return self.user.tariff_history.filter(
            is_active=True,
            wave__isnull=False
        ).exists()

    @cached_property
    def is_active(self):
        return self.tariff is not None

    @cached_property
    def is_in_club(self):
        if not self.is_active:
            return False

        return self.tariff.tariff_group.is_in_club

    @cached_property
    def valid_until(self):
        last_record = self.last_active_tariff_history_record
        if last_record:
            return last_record.valid_until

        return None

    @cached_property
    def communication_mode(self):
        th = self.active_tariff_history or self.next_tariff_history
        if th:
            tg = th.tariff.tariff_group
            if tg.is_wave:
                return tg.communication_mode

        return None

    @property
    def has_full_bot_access(self):
        th = self.active_tariff_history or self.next_tariff_history
        if th:
            return th.tariff.tariff_group.bot_access == TariffGroup.BOT_ACCESS_FULL_MODE

        return False

    # текущая активная подписка пользователя
    @property
    def active_subscription(self):
        return self.user.subscriptions.filter(
            Q(status=Subscription.STATUS_ACTIVE) |
            (
                Q(status=Subscription.STATUS_CANCELED)
                &
                Q(
                    payments__tariff_history__valid_until__gte=date.today(),
                    payments__tariff_history__is_active=True,
                )
                # не надо ли тут напрямую через ТХ все же у юзера? всегда ли будет пеймент?
            )
        ).order_by('-id').first()

    @property
    def subscription_valid_until(self):
        if self.active_subscription:
            return self.active_subscription.valid_until

        return None

    @property
    def tariff_renewal_from(self):
        if self.tariff and self.tariff.tariff_group.is_wave:
            return self.active_tariff_history.valid_until - timedelta(days=24)
        else:
            return None

    @property
    def tariff_renewal_until(self):
        if self.tariff and self.tariff.tariff_group.is_wave:
            return self.active_tariff_history.valid_until
        else:
            return None

    def __init__(self, *args, **kwargs):
        super(Profile, self).__init__(*args, **kwargs)
        self.__stat_group_orig = self.stat_group
        self.__tariff_next_orig = self.tariff_next

    @cached_property
    def last_active_tariff_history_record(self):
        """

        :rtype: crm.models.TariffHistory
        """

        # интересует последняя оплаченная запись,
        # проверяем на наличие next, потом acnive и только потом уже делаем запрос
        if self.next_tariff_history:
            return self.next_tariff_history

        if self.active_tariff_history:
            return self.active_tariff_history

        th_filter = self.user.tariff_history.filter(
            is_active=True,
            valid_until__lt=date.today()
        ).select_related('tariff', 'tariff__tariff_group', 'wave')

        return th_filter.order_by('-valid_until').first()

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        _mode = 'UPDATE' if self.id else 'INSERT'

        super(Profile, self).save(force_insert, force_update, *args, **kwargs)

        if _mode == 'INSERT':
            stat_group_log = StatGroupHistory(
                user=self.user,
                active_from=None,
                active_until=None,
                stat_group=self.stat_group
            )
            stat_group_log.save()

        if self.tariff_next != self.__tariff_next_orig:
            with transaction.atomic():
                # Locking
                Profile.objects.select_for_update().get(user=self.user)

                # больше одного не будет
                order = Payment.objects.filter(
                    user=self.user,
                    status=Payment.STATUS_PENDING
                ).first()

                if order:
                    order.status = Payment.STATUS_CANCELED
                    order.save(update_fields=['status'])

            self.__tariff_next_orig = self.tariff_next

        if self.stat_group != self.__stat_group_orig:
            last_record = StatGroupHistory.objects.filter(
                user=self.user, stat_group=self.__stat_group_orig,
                active_until__isnull=True
            ).first()

            if last_record:
                last_record.active_until = date.today() - timedelta(days=1)
                last_record.save()
                next_start_date = date.today()
            else:
                next_start_date = None

            StatGroupHistory(
                user=self.user, stat_group=self.stat_group, active_from=next_start_date, active_until=None
            ).save()

            self.__stat_group_orig = self.stat_group

    def __str__(self):
        return '%s (%s)' % (self.user.username, self.wave.title if self.wave else 'Не является участником проекта')

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.user.username)

    def deactivate(self):
        profile_user = self.user
        user_chats = profile_user.membership.exclude(status='BANNED').exclude(chat__is_active=False)

        for _chat in user_chats:
            _chat.status = 'BANNED'
            _chat.save()

        # self.is_active = False
        self.save()


def activate_participant(sender, instance, created, raw, using, update_fields, **kwargs):
    """

    :param sender:
    :param update_fields:
    :param instance:
    :type instance: Profile
    :param kwargs:
    :return:
    """

    if created:
        from crm.models import Application
        try:
            Application.objects.get(user=instance.user)
        except Application.DoesNotExist:
            application = Application(user=instance.user)
            application.save()

    if instance.tariff_next_id:
        if not instance.user.application.is_payment_allowed:
            instance.user.application.is_payment_allowed = True
            instance.user.application.save(update_fields=['is_payment_allowed'])
            LogEntry.objects.log_action(
                user_id=settings.SYSTEM_USER_ID,
                content_type_id=ContentType.objects.get_for_model(instance.user.application).pk,
                object_id=instance.user.application,
                object_repr=instance.user.username,
                action_flag=CHANGE,
                change_message="Enable payment for user with tariff-next"
            )
    else:
        if instance.user.application.is_payment_allowed:
            instance.user.application.is_payment_allowed = False
            instance.user.application.save(update_fields=['is_payment_allowed'])
            LogEntry.objects.log_action(
                user_id=settings.SYSTEM_USER_ID,
                content_type_id=ContentType.objects.get_for_model(instance.user.application).pk,
                object_id=instance.user.application,
                object_repr=instance.user.username,
                action_flag=CHANGE,
                change_message="Disable payment for user with tariff-next"
            )


post_save.connect(activate_participant, sender=Profile)
