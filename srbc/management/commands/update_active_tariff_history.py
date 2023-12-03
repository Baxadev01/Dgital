from django.core.management.base import BaseCommand
from django.db import connection, IntegrityError
from django.utils.timezone import localtime


class Command(BaseCommand):
    help = "заменяет истекшие active_tariff_history на новые значения"

    def handle(self, *args, **options):
        # обновляем в 2 этапа

        # скинем все записи,у которых valid_until в прошлом и нет next_tariff_history
        # исходим из того, что если есть и next и active, то они встык, нет смысла сначала скидывать,
        # а потом менять
        QUERY_CLEAR = """
update srbc_profile profile
set active_tariff_history_id = NULL
from crm_tariffhistory th
where profile.active_tariff_history_id = th.id
    and valid_until < %s"""

        # для пользователей с next_tariff_history проверяем не настало ли его время
        QUERY_SET = """
update srbc_profile profile
set active_tariff_history_id = next_tariff_history_id,
    next_tariff_history_id = NULL
from crm_tariffhistory th
where profile.next_tariff_history_id = th.id
and valid_from <= %s"""

        with connection.cursor() as cursor:
            try:
                print("Local time: %s" % localtime())
                print("Local date: %s" % localtime().date())
                cursor.execute(QUERY_SET, [localtime().date(), ])
                print('QUERY_SET: %s' % cursor.query)
                cursor.execute(QUERY_CLEAR, [localtime().date(), ])
                print('QUERY_CLEAR: %s' % cursor.query)
            except IntegrityError as e:
                print("ERROR occurred while updating active_tariff_history")

        print("task finished")
