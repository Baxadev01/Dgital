from django.core.management.base import BaseCommand

from srbc.models import DiaryRecord, DiaryRecordAnalysis
from srbc.utils.meal_containers import get_diary_analysis


class Command(BaseCommand):
    help = "Заполняет таблицу DiaryRecordAnalysis по таблице DiaryRecord"

    def handle(self, *args, **options):
        # получаем все записи, с флагом is_meal_reviewed
        diaries = DiaryRecord.objects.filter(
            is_meal_reviewed=True,
            analysis__isnull=True,
            wake_up_time__isnull=False,
            bed_time__isnull=False,
        ).exclude(meal_status='FAKE').order_by('-date').all()

        for diary in diaries:
            diary_analysis = get_diary_analysis(diary)

            if diary_analysis:
                DiaryRecordAnalysis.objects.update_or_create(
                    diary=diary, defaults={
                        'containers': diary_analysis['containers'],
                        'day_stat': diary_analysis['day_stat']
                    }
                )
