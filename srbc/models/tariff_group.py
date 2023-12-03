from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('TariffGroup',)


class TariffGroup(models.Model):
    MEETINGS_NO_ACCESS = 'NONE'
    MEETINGS_NEWBIE = 'NEWBIE'
    MEETINGS_ALL = 'ALL'

    OPTIONS_MEETINGS_ACCESS = (
        (MEETINGS_NO_ACCESS, _('Нет доступа')),
        (MEETINGS_NEWBIE, _('Доступ к новичковым митингам')),
        (MEETINGS_ALL, _('Доступ ко всем митингам')),
    )

    DIARY_ACCESS_READ = 'READ'
    DIARY_ACCESS_WRITE = 'WRITE'
    DIARY_ACCESS_ANLZ_AUTO = 'ANLZ_AUTO'
    DIARY_ACCESS_ANLZ_MANUAL = 'ANLZ_MANUAL'

    OPTIONS_DIARY_ACCESS = (
        (DIARY_ACCESS_READ, _('Чтение')),
        (DIARY_ACCESS_WRITE, _('Запись')),
        (DIARY_ACCESS_ANLZ_AUTO, _('Автоматический анализ')),
        (DIARY_ACCESS_ANLZ_MANUAL, _('Ручной анализ')),
    )

    DIARY_ANALYZE_MANUAL = 'MANUAL'
    DIARY_ANALYZE_AUTO = 'AUTO'
    DIARY_ANALYZE_BY_REQUEST = 'BY_REQUEST'
    DIARY_ANALYZE_NO = 'NO'

    OPTIONS_DIARY_ANALYZE = (
        (DIARY_ANALYZE_MANUAL, _('Ручной')),
        (DIARY_ANALYZE_AUTO, _('Автоматический')),
        (DIARY_ANALYZE_BY_REQUEST, _('По запросу')),
        (DIARY_ANALYZE_NO, _('Отсутствует')),
    )

    COMMUNICATION_MODE_CHAT = 'CHAT'
    COMMUNICATION_MODE_CHANNEL = 'CHANNEL'

    OPTIONS_COMMUNICATION_MODE = (
        (COMMUNICATION_MODE_CHAT, _('Чат')),
        (COMMUNICATION_MODE_CHANNEL, _('Канал')),
    )

    BOT_ACCESS_FULL_MODE = 'FULL'
    BOT_ACCESS_BASE_MODE = 'BASE'

    OPTIONS_BOT_ACCESS = (
        (BOT_ACCESS_FULL_MODE, _('Полный доступ')),
        (BOT_ACCESS_BASE_MODE, _('Базовый доступ')),
    )

    title = models.CharField(max_length=255)

    communication_mode = models.CharField(
        max_length=20, blank=True, null=True,
        choices=OPTIONS_COMMUNICATION_MODE
    )

    diary_analyze_mode = models.CharField(
        max_length=20, blank=True, null=True,
        choices=OPTIONS_DIARY_ANALYZE
    )

    analysis_min_days = models.IntegerField(blank=True, default=0)

    questions_per_day = models.IntegerField(blank=True, default=0)

    checkpoints_required = models.CharField(
        max_length=20,
        choices=(
            ('ALWAYS', "Каждые 2 недели"),
            ('BMI', "Каждые две недели при выходе за норму ИМТ"),
            ('NEVER', "Нет требований"),
        )
    )

    diary_data_required = models.IntegerField(blank=True, default=0)
    diary_meals_required = models.IntegerField(blank=True, default=0)

    meetings_access = models.CharField(
        max_length=20,
        choices=OPTIONS_MEETINGS_ACCESS
    )

    kb_access = models.BooleanField(blank=True, default=False)
    is_wave = models.BooleanField(blank=True, default=False)
    is_in_club = models.BooleanField(blank=True, default=False)

    expertise_access = models.BooleanField(blank=True, default=False)

    diary_access = models.CharField(
        max_length=20,
        choices=OPTIONS_DIARY_ACCESS,
        default=DIARY_ACCESS_READ
    )

    bot_access = models.CharField(
        max_length=20,
        choices=OPTIONS_BOT_ACCESS,
        default=BOT_ACCESS_FULL_MODE
    )

    def __str__(self):
        return '%s (#%s)' % (self.title, self.pk)
