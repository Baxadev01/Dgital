# -*- coding: utf-8 -*-
import logging
import math
from datetime import datetime, timedelta
from decimal import Decimal
from time import time as posix_time

from dateutil import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, DateField, F, Q
from django.http.response import Http404, HttpResponseBadRequest
from django.utils import timezone
from django.utils.timezone import localdate
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_tracking.mixins import LoggingMixin
from drf_yasg.utils import swagger_auto_schema

from swagger_docs import swagger_docs
from srbc.models import Checkpoint, DiaryMealFault, DiaryRecord, DiaryRecordAnalysis, SRBCImage, User, UserReport
from srbc.serializers.general import NewDiaryMealFaultsSerializer
from srbc.tasks import generate_results_report
from srbc.utils.diary import calculate_user_stat
from srbc.utils.helpers import pluralize
from srbc.utils.meal_containers import get_meal_containers, get_diary_analysis
from srbc.utils.meal_parsing import get_meal_faults
from srbc.utils.meal_recommenation import get_recommendation_fulfillment
from srbc.utils.permissions import IsActiveUser, HasExpertiseAccess, IsWaveUser

logger = logging.getLogger('ANALYTICS_API')


class DiaryStatView(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsActiveUser)

    @staticmethod
    @swagger_auto_schema(
            **swagger_docs['GET /v1/diary/{user_id}/stat/meals/']
    )
    def get_meals_faults_stat(request, user_id):
        """
            Получение общей статистики действий по накоплению жира у выбранного пользователя
        """
        if not request.user.is_staff:
            if user_id != "%s" % request.user.pk:
                raise Http404()

        queryset = DiaryMealFault.objects.filter(diary_record__user_id=user_id)

        try:
            start_date = request.GET.get('start')
            end_date = request.GET.get('end')
            if start_date:
                queryset = queryset.filter(diary_record__date__gte=DateField().to_python(start_date))

            if end_date:
                queryset = queryset.filter(diary_record__date__lte=DateField().to_python(end_date))

        except Exception:
            raise Http404()

        queryset = queryset.values('fault_id') \
            .annotate(
            days_count=Count('diary_record__date', distinct=True),
            faults_count=Count('id', distinct=True),
            title=F('fault__title')
        ).order_by('fault_id')

        return Response(list(queryset))

    @staticmethod
    def _process_date_for_stat(d):
        try:
            d = int(float(d) / 1000)
        except ValueError:
            # start_date is NaN or
            # start_date is string
            d = 0
        return d

    @staticmethod
    @swagger_auto_schema(
            **swagger_docs['GET /v1/diary/{user_id}/stat/user/']
    )
    def get_user_stat(request, user_id):
        """
            Получить общую статистику участия пользователя за период (по умолчанию - с 01.01.1970 по настоящий момент)
        """
        if not request.user.is_staff:
            if user_id != str(request.user.pk):
                raise Http404()

        start_date = request.GET.get('start') or 0
        end_date = request.GET.get('end') or posix_time()
        start_date = DiaryStatView._process_date_for_stat(start_date)
        end_date = DiaryStatView._process_date_for_stat(end_date)

        start_date = datetime(1970, 1, 1) + timedelta(seconds=start_date)
        end_date = datetime(1970, 1, 1) + timedelta(seconds=end_date)
        data = calculate_user_stat(user_id=int(user_id), start_date=start_date.date(), end_date=end_date.date())
        return Response(data)


def set_task_for_report_generation(user, force=False):
    """
        Ставит задачу на подсчет отчета если:
        - нет отчета за день
        - если решили пересчитать отчет снова (force == True)
    """
    report = UserReport.objects.filter(user_id=user.pk, date=localdate()).first()
    if report is None:
        report = UserReport(
            date=localdate(),
            user=user
        )

        report.save()
        # ставим задачу на подсчет отчета
        generate_results_report.delay(report_id=report.id)
    else:
        if force:
            # отчет существует, но решили пересчитать его (например, поправили багу и из админки запустили)
            generate_results_report.delay(report_id=report.id, force=True)

    return report


def result_notice_gen(user):
    """

    :param user:
    :type user: srbc.models.User
    :return:
    """

    text_template = """Период: {two_weeks_start}-{two_weeks_end}	 
дней с данными: {data_count}  
дней с представленными рационами: {meals_count}    
контрольные коллажи: {photo_flag}  
контрольные замеры: {measure_flag}  

Δ веса: {weight_delta:.1f} кг ({weight_delta_prc:.0f}%; ИМТ {bmi_start:.1f} → {bmi_current:.1f})  
{measure_stat}  
дней с жиронакопительными действиями: {fault_days_count}    
дней с дополнительными продуктами: {overcalory_days_count}{pers_rec_days_text}  
жиронакопительные действия: {faults_count}  
{faults_stat}  
в дни с представленными данными система питания соответствует концепции selfrebootcamp на {ok_meals_prc:.0f}%    
  
выполнение нормы активности: {steps_ok} {steps_title} из {steps_count} ({steps_ok_prc:.0f}%)  
{steps_other_stat}  
степень достоверности рекомендаций (определяется по количеству дней с предоставленными данными): {data_completion:.0f}%    
  
Рекомендации, которые вы получите, достоверны только в случае, если вы предоставляли точные данные и в дни с пропусками рационы не отличались от представленных.
  
Рекомендации не достоверны, если представленные вами данные ложны (не указана часть продуктов, указаны лишние, искажены интервалы или указаны навески, отличающиеся от реальных), а также если в дни без предоставления данных рационы отличались от представленных.
"""

    pers_rec_days_template = """
\nдней, соответствующих персональным рекомендациям: {pers_rec_ok_days} из {pers_rec_total_days} ({pers_rec_ok_prc:.0f}%) 
    """

    today = timezone.now()

    start = today - timedelta(days=(today.weekday() + 1) % 7)
    two_weeks_end = start + relativedelta.relativedelta(weekday=relativedelta.SU(-1))
    two_weeks_start = two_weeks_end - timedelta(days=13)

    two_weeks_start = two_weeks_start.date()
    two_weeks_end = two_weeks_end.date()

    checkpoint_min_date = two_weeks_end - timedelta(days=2)

    measurement_last = Checkpoint.objects.filter(
        user=user, date__gte=checkpoint_min_date, is_measurements_done=True
    ).order_by('-date').first()

    measurement_first = Checkpoint.objects.filter(
        user=user, is_measurements_done=True
    ).order_by('date').first()

    measure_stat = ''
    if measurement_last:
        measure_stat = "Δ объемов: %sсм (%s → %s)  \n" % (
            Decimal(measurement_first.measurements_sum - measurement_last.measurements_sum) / 10,
            Decimal(measurement_first.measurements_sum) / 10,
            Decimal(measurement_last.measurements_sum) / 10,
        )

    photo_exists = SRBCImage.objects.filter(
        user=user, date__gte=checkpoint_min_date,
        image_type__in=['CHECKPOINT_PHOTO', 'CHECKPOINT_PHOTO_FRONT', 'CHECKPOINT_PHOTO_SIDE', 'CHECKPOINT_PHOTO_REAR']
    ).exists()

    user_meals = DiaryRecord.objects.filter(meal_status='DONE', user=user,
                                            date__gte=two_weeks_start, date__lte=two_weeks_end)
    meals_count = user_meals.count()

    # meals_prc = Decimal(meals_count) / Decimal(14) * Decimal(100)

    data_count = DiaryRecord.objects.filter(
        user=user,
        date__gte=two_weeks_start, date__lte=two_weeks_end,
        steps__isnull=False,
        sleep__isnull=False,
        weight__isnull=False
    ).count()

    meals_data_count = user_meals.filter(
        steps__isnull=False,
        sleep__isnull=False,
        weight__isnull=False
    ).count()

    meals_no_data_count = user_meals.filter(
        Q(steps__isnull=True) |
        Q(sleep__isnull=True) |
        Q(weight__isnull=True)
    ).count()

    data_prc = (Decimal(meals_data_count) + Decimal(meals_no_data_count) / 2) / Decimal(14) * 100

    pers_rec_total_days = user_meals.filter(pers_rec_flag__in=['F', 'OK']).count()
    pers_rec_ok_days = user_meals.filter(pers_rec_flag__in=['OK']).count()
    pers_rec_ok_prc = Decimal(pers_rec_ok_days) / Decimal(pers_rec_total_days) * 100 if pers_rec_total_days else 0

    overcalory_meals_count = user_meals.filter(is_overcalory=True).count()
    ok_meals_count = user_meals.filter(is_ooc=0, faults=0).count()
    if meals_count:
        ok_meals_prc = Decimal(ok_meals_count) / Decimal(meals_count) * Decimal(100)
    else:
        ok_meals_prc = 0

    steps_filter = DiaryRecord.objects.filter(user=user, steps__isnull=False,
                                              date__gte=two_weeks_start, date__lte=two_weeks_end)
    steps_count = steps_filter.count()
    steps_count_ok = steps_filter.filter(steps__gte=10000).count()
    if steps_count:
        steps_ok_prc = Decimal(steps_count_ok) / Decimal(steps_count) * Decimal(100)
    else:
        steps_ok_prc = 0

    steps_quant = 0.5
    steps_get = math.floor((steps_count - steps_count_ok) * steps_quant)
    steps_other = ''

    if steps_get:
        steps_other = steps_filter.order_by('steps').all()[steps_get:steps_get + 1].get()
        steps_other = Decimal(steps_other.steps) / 100
        steps_other = "Остальные дни: %.0f%%  \n" % steps_other

    start_weight = 0
    last_weight = 0
    weight_delta = 0

    start_diary = DiaryRecord.objects.filter(
        user=user,
        weight__isnull=False,
        date__gte=two_weeks_start, date__lte=two_weeks_end
    ).order_by('date').first()

    last_diary = DiaryRecord.objects.filter(
        user=user, weight__isnull=False,
        date__gte=two_weeks_start,
        date__lte=two_weeks_end
    ).order_by('-date').first()

    height = user.profile.height
    start_bmi = 0
    last_bmi = 0

    if height:
        if start_diary:
            start_weight = start_diary.weight
            start_bmi = start_weight / ((Decimal(height) / 100) ** 2)

        if last_diary:
            last_weight = last_diary.weight
            last_bmi = last_weight / ((Decimal(height) / 100) ** 2)

    if start_weight:
        weight_delta = last_weight - start_weight

    faults_stat = DiaryMealFault.objects.filter(
        diary_record__user_id=user.pk,
        diary_record__date__gte=two_weeks_start,
        diary_record__date__lte=two_weeks_end,
        fault__is_public=True
    ).values('fault_id').annotate(
        days_count=Count('diary_record__date', distinct=True),
        faults_count=Count('id', distinct=True),
        title=F('fault__title')
    ).order_by('fault_id')
    faults_stat = list(faults_stat)
    faults_stat_txt = ''
    if len(faults_stat):
        faults_stat_bits = ["* %s (%s)  \n" % (f['title'], f['faults_count']) for f in faults_stat]
        faults_stat_txt = '\n%s' % ''.join(faults_stat_bits)

    # Get charts data
    diaries = DiaryRecord.objects.filter(
        user_id=user.pk,
        date__gte=two_weeks_start,
        date__lte=two_weeks_end
    )

    faults_count = 0
    for diary in diaries:
        if diary.is_ooc:
            faults_count += 3
        else:
            if diary.faults:
                faults_count += diary.faults

    steps_title = pluralize(steps_count_ok, ['день', 'дня', 'дней'])

    if pers_rec_total_days:
        pers_rec_days_text = pers_rec_days_template.format(
            pers_rec_ok_days=pers_rec_ok_days,
            pers_rec_total_days=pers_rec_total_days,
            pers_rec_ok_prc=pers_rec_ok_prc
        )
    else:
        pers_rec_days_text = ''

    result = text_template.format(
        two_weeks_start=two_weeks_start.__format__('%d/%m'),
        two_weeks_end=two_weeks_end.__format__('%d/%m'),
        meals_count=meals_count,
        data_count=data_count,
        fault_days_count=meals_count - ok_meals_count,
        overcalory_days_count=overcalory_meals_count,
        pers_rec_days_text=pers_rec_days_text,
        faults_count=faults_count,
        faults_stat=faults_stat_txt,
        weight_delta=weight_delta,
        weight_delta_prc=100 * weight_delta / start_weight if start_weight else 0,
        bmi_start=start_bmi,
        bmi_current=last_bmi,
        measure_stat=measure_stat,
        steps_ok=steps_count_ok,
        steps_title=steps_title,
        steps_count=steps_count,
        steps_ok_prc=steps_ok_prc,
        steps_other_stat=steps_other,
        photo_flag="есть" if photo_exists else "не предоставлены",
        measure_flag="есть" if measurement_last else "не предоставлены",
        ok_meals_prc=ok_meals_prc,
        data_completion=data_prc
    )

    # logging.info(result)
    return result


class ReportView(LoggingMixin, viewsets.ViewSet):
    permission_classes = (IsAuthenticated, IsActiveUser, IsWaveUser, HasExpertiseAccess,)

    @swagger_auto_schema(
        **swagger_docs['GET /v1/diary/{user_id}/stat/report/']
    )
    def get_stat_report_admin(self, request, user_id):
        """
            Сгенерировать для пользователя PDF-отчет со статистикой участия
        """
        return self.get_stat_report(request, user_id)

    @staticmethod
    def get_stat_report(request, user_id=None):
        """
            Сгенерировать для пользователя PDF-отчет со статистикой участия
        """
        if not user_id:
            user = request.user
        elif request.user.is_staff:
            user = User.objects.get(pk=user_id)
        else:
            return HttpResponseBadRequest()

        report = set_task_for_report_generation(user)

        return Response({
            "hashid": report.hashid,
        })


class ParseMealView(LoggingMixin, viewsets.ViewSet):
    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/user/{user_id}/diaries/{diary_date}/meal_review/']
    )
    def get_meal_faults_by_date(request, user_id, diary_date):
        """
            Получение списка действий по накоплению жира в выбранном рационе у выбранного пользователя
        """
        if not request.user.is_staff:
            raise Http404()

        diary = DiaryRecord.objects.filter(user_id=user_id, date=diary_date).first()

        if not diary:
            raise Http404()

        faults_list, error = get_meal_faults(diary)
        pers_rec_status, rec_faults_list = get_recommendation_fulfillment(diary)
        containers, meals_msg_codes, meals_msg_text, is_report_reliable = get_meal_containers(diary)
        if error:
            return Response(error)

        faults_data = NewDiaryMealFaultsSerializer(many=True, instance=faults_list).data

        return Response({
            "status": 'OK',
            "data": faults_data,
            "rec_status": pers_rec_status,
            "rec_faults": rec_faults_list,
            "containers": containers,
            "messages": meals_msg_codes,
            "report": meals_msg_text,
            "is_report_reliable": is_report_reliable,
        })

    @staticmethod
    @swagger_auto_schema(
        **swagger_docs['GET /v1/user/{user_id}/diaries/{diary_date}/meal_stat/']
    )
    def get_meal_stat_by_date(request, user_id, diary_date):
        """
            Получение анализа рациона пользователя
        """
        diary = DiaryRecord.objects.filter(user_id=user_id, date=diary_date).first()

        if not diary:
            raise Http404()

        if not diary.is_meal_reviewed:
            return Response({'error': "Diary is not reviewed yet"})
        
        try:
            diary_analysis = DiaryRecordAnalysis.objects.get(diary=diary.pk)
            return Response({
                'containers': diary_analysis.containers,
                'day_stat': diary_analysis.day_stat
            })
        except ObjectDoesNotExist:
            # если не нашли, то запрашиваем анализ
            diary_analysis = get_diary_analysis(diary)
            if diary_analysis:
                return Response({
                    'containers': diary_analysis.get('containers'),
                    'day_stat': diary_analysis.get('day_stat'),
                })
            else:
                raise Http404() 

