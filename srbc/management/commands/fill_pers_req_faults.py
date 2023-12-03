from django.core.management.base import BaseCommand

from srbc.models import DiaryRecord
from srbc.utils.meal_recommenation import get_recommendation_fulfillment

class Command(BaseCommand):
    help = "Заполняет с поле pers_rec_flag в таблице DiaryRecord"

    def handle(self, *args, **options):
        # поулчаем все записи, с флагом невыполненности персональных рекоммендаций
        diaries = DiaryRecord.objects.filter(pers_rec_flag=DiaryRecord.PERS_REC_F).all()

        for diary in diaries:
            _ , rec_faults_list = get_recommendation_fulfillment(diary)

            if not rec_faults_list:
                # если в записи указано, что есть ошибки, но функция их не нахожит - просто сигнализиурем об этом
                print("user %s. diary id = %s, diary date = %s" % (diary.user.id, diary.pk, diary.date))
            else:
                diary.pers_req_faults = rec_faults_list
                diary.save(update_fields=['pers_req_faults'])
