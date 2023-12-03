from dateutil.relativedelta import relativedelta, FR

from django.core.management.base import BaseCommand
from django.db.models import F

from srbc.models import User, Profile
from crm.models import TariffHistory, Payment, Order


class Command(BaseCommand):
    help = "Заполняет с 0 таблицу tariff_history"

    def handle(self, *args, **options):
        # Все пользователи, у которых есть WAVE - запись от srbc_profile.wave.start_date до srbc_profile.valid_until

        # почистим
        TariffHistory.objects.all().delete()

        profiles = Profile.objects.filter(wave__isnull=False).all()

        for profile in profiles:
            # TODO не знаю откуда еще брать тариф, если не из профайла, а там его много где нету
            # добавлять без него очень странно
            if profile.tariff and profile.valid_until:
                item = TariffHistory()
                item.valid_from = profile.wave.start_date
                item.valid_until = profile.valid_until
                item.is_active = True
                # TODO тут не совсем ясно. как понимаю у одного wave может быть много платежей, пока беру последний,
                # мб стоит логику пересмотреть заполнения
                item.payment = Payment.objects.filter(wave=profile.wave, user=profile.user).order_by('-id').first()
                item.tariff = profile.tariff
                item.user = profile.user
                item.wave = profile.wave
                item.save()

        # Все записи из crm_order у которых crm_order.paid_until < crm_order.user.profile.wave.start_date -
        # добавить длительностью 8 недель, заканчивающихся в дату paid_until (дата начала - всегда пятница)

        # берем данные из старой таблицы
        orders = Order.objects.filter(paid_until__lt=F('user__profile__wave__start_date'), status='APPROVED').all()

        for order in orders:
            if order.user.profile.tariff and order.user.profile.valid_until:
                item = TariffHistory()

                item.valid_from = order.paid_until + relativedelta(weekday=FR(-8))

                item.valid_until = order.paid_until
                item.status = "PAID"  # TODO вынести в енумчик
                item.payment_id = order.pk  # айди совпадают в старой и новой таблицах
                item.tariff = order.user.profile.tariff
                item.user = order.user
                item.wave = order.wave
                item.save()

        print('Data were transferred')
