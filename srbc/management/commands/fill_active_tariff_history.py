

from django.db import connection, IntegrityError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "заполняет поле active_tariff_history и next_tariff_history в профайле"

    def handle(self, *args, **options):

        QUERY = """
            update srbc_profile profile
            set active_tariff_history_id = (select id from crm_tariffhistory th
                                            where th.user_id = profile.user_id and valid_from <= NOW()::date and valid_until >= NOW()::date and is_active = True
                                            order by valid_until desc
                                            limit 1),
            next_tariff_history_id = (select id from crm_tariffhistory th
                                            where th.user_id = profile.user_id and valid_from > NOW()::date and is_active = True
                                            order by valid_until asc
                                            limit 1)
        """
        with connection.cursor() as cursor:
            try:
                cursor.execute(QUERY, {})
            except IntegrityError as e:
                print("ERROR occurred while updating active_tariff_history")

        print("task finished")
