from datetime import date

from django.core.management.base import BaseCommand
from django.db import connection, IntegrityError
from django.db.models import Prefetch, Q

from srbc.models import Profile
from crm.models import TariffHistory


class Command(BaseCommand):
    help = "проверяет поля в Profile на соотвествие в Tariff_history и tariff_group"

    def add_arguments(self, parser):
        parser.add_argument('--tariff', action='store_true', dest='tariff')
        parser.add_argument('--duration', action='store_true', dest='duration')
        parser.add_argument('--history', action='store_true', dest='history')
        parser.add_argument('--payments', action='store_true', dest='payments')

    def get_duplicated_payments(self):

        QUERY = """
            select * from (
                Select payment_id, count(*) as rows_count from crm_tariffhistory group by payment_id
            ) dups
            where
            dups.rows_count > 1 and payment_id is not NULL
        """
        with connection.cursor() as cursor:
            try:
                cursor.execute(QUERY, {})
                return cursor.fetchall()
            except IntegrityError as e:
                print("ERROR occurred while checking for duplication payments")
                return []

    def handle(self, *args, **options):
        check_tariff = options.get('tariff', False)
        check_duration = options.get('duration', False)
        check_history = options.get('history', False)
        check_payments = options.get('payments', False)

        today = date.today()

        profiles = Profile.objects.prefetch_related(
            Prefetch('user__tariff_history', TariffHistory.objects.filter(
                is_active=True,
                valid_until__gte=today,
                valid_from__lte=today
            ).select_related('tariff__tariff_group'),
                to_attr='active_tariff_history_records')
        ).all()

        for profile in profiles:
            active_tariff_history_record = None

            if profile.user.active_tariff_history_records:

                # проверим и выведем случай, когда несколько тарифов активны у пользователя (не должно так быть)
                if len(profile.user.active_tariff_history_records) > 1:
                    # отдельно проверим случай о продлении
                    # записей должно быть 2, должен быть одинаковым тариф,
                    # дата последней записи больше предыдущей
                    records = sorted(
                        profile.user.active_tariff_history_records,
                        key=lambda el: el.valid_until,
                        reverse=True
                    )

                    th_last = profile.user.active_tariff_history_records[0]
                    th_prev = profile.user.active_tariff_history_records[1]

                    if len(profile.user.active_tariff_history_records) == 2 \
                            and th_last.valid_from >= th_prev.valid_until:
                        # and th_last.tariff == th_prev.tariff \

                        active_tariff_history_record = records[0]
                    else:
                        if check_history:
                            print("user %s. Multiple active tariffs" % profile.user.id)
                        continue
                else:
                    active_tariff_history_record = profile.user.active_tariff_history_records[0]

            # проверяем тарифы
            if profile.tariff:
                # для уже не активных юзеров - не выводим ошибку
                if not active_tariff_history_record:
                    if profile.valid_until and profile.valid_until >= today:
                        if check_tariff:
                            print("user %s. Different tariffs. Profile tariff = %s, history tariff = %s" %
                                  (profile.user.id, profile.tariff, None))
                    continue

                if profile.tariff.pk != active_tariff_history_record.tariff_id:
                    if check_tariff:
                        print("user %s. Different tariffs. Profile tariff = %s, history tariff = %s" %
                              (profile.user.id, profile.tariff, active_tariff_history_record.tariff))
                    continue
                else:
                    # тарифы совпали, проверяем дату окончания
                    # FIXME: если уже есть новая tariff history в будущее - то в профиле будет продленная дата и выдаст ошибку
                    if active_tariff_history_record.valid_until != profile.valid_until:
                        if check_duration:
                            print("user %s. Different until date. Profile date = %s, history date = %s" %
                                  (profile.user.id, profile.valid_until, active_tariff_history_record.valid_until))
                        continue

                    # проверяем на совпадение communication-mode
                    if profile.communication_mode != active_tariff_history_record.tariff.tariff_group.communication_mode:
                        if check_tariff:
                            print("user %s. Different communication mode. Profile mode = %s, history mode = %s" % (
                                profile.user.id, profile.communication_mode,
                                active_tariff_history_record.tariff.tariff_group.communication_mode))
                        continue
            else:
                # в профайле нет тарифа, а в тариф хистори есть активный
                if active_tariff_history_record:
                    if check_tariff:
                        print("user %s. Different tariffs. Profile tariff = %s, history tariff = %s" %
                              (profile.user.id, None, active_tariff_history_record.tariff))
                    continue

        # проверка на повторяющиеся платежи в тарифф хистори
        if check_payments:
            data = self.get_duplicated_payments()
            if len(data):
                print("duplicated payments in tariff_history:")
                for item in data:
                    print("payment_id %s. count= %s" %
                          (item[0], item[1]))
            else:
                print("Duplicated payments not found")

        print("task finished")
