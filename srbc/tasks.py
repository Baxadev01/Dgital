# -*- coding: utf-8 -*-

import io
import json
import logging
import math
import os
import tempfile
import uuid
from datetime import timedelta, datetime
from decimal import Decimal
from subprocess import Popen, PIPE

import pdfkit
import pytz
import qrcode
import qrcode.image.svg
from PIL import Image
from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile, File
from django.db import transaction
from django.db.models import Count, F
from django.template import loader
from django.utils import timezone, dateformat
from django_telegrambot.apps import DjangoTelegramBot

from .celery import app
from content.utils import store_dialogue_reply
from srbc.models import (
    Checkpoint, SRBCImage, User, DiaryRecord, DiaryMealFault,
    UserReport, Profile, CheckpointPhotos, DiaryMeal, MealComponent)
from srbc.utils.checkpoint_measurement import collect_image_info
from srbc.utils.helpers import pluralize
from srbc.utils.srbc_image import (
    put_image_in_memory, save_image, build_3view_collage,
    build_compare_collages, create_meal_collage as _create_meal_collage, get_meal_components_text)

from srbc.utils.diary import get_checkpoint_photo_set
from srbc.views.collage import generate_data_image

from celery import Celery, states
from celery.exceptions import Ignore


logger = logging.getLogger(__name__)


# TODO: перестроить структуру, когда появятся еще таски (может разбить по папкам типа tasks/analytics, tasks/telegram и тд)
# TODO: PR для туду выше уже есть - надо смержиться с ним

@app.task()
def generate_results_report(report_id, notify_user=True, force=False):
    """ Задача для обработки подсчета пользовательских отчетов.

    :param report_id:
    :type report_id: int
    :param notify_user: if True then sends message to telegram
    :type notify_user: bool
    :param force: if True then regenerates report even if pdf_file already exists
    :type force: bool
    :return:
    """
    assert isinstance(report_id, int)
    assert isinstance(notify_user, bool)

    new_report_done = False
    try:
        with transaction.atomic():
            report = UserReport.objects.select_for_update().get(id=report_id)

            if force or not report.pdf_file:
                _generate_results_report(report)
                new_report_done = True

    except UserReport.DoesNotExist:
        logger.error('Report does not exist', extra={'report_id': report_id})
        return

    except Exception as exc:
        # Узнаем об ошибке. После ее устранения запустим сборку отчета из админки.
        logger.exception(exc)
        # self.retry(countdown=60 * self.request.retries, exc=exc, report_id=report_id)

    else:
        # все прошло успешно
        if notify_user and new_report_done:
            # pdf_url = report.pdf_file.url
            report_notification = "В личном кабинете подготовился новый отчет. \n\n" \
                                  "Для просмотра, пожалуйста, [перейдите в ЛК](https://lk.selfreboot.camp/reports/) " \
                                  "или [по прямой ссылке на отчет](%s)" % report.pdf_file.url

            send_notification.delay(chat_id=report.user.profile.telegram_id, content=report_notification)


def _generate_results_report(report):
    """ Собирает данные для пользовательского отчета.

    :param report: report obj
    :type report: srbc.models.UserReport
    """
    user = report.user
    start_date = user.profile.wave.start_date

    days_passed = (timezone.now().date() - start_date).days
    weeks_passed = math.ceil(days_passed / 7.0)

    user_meals = DiaryRecord.objects.filter(is_fake_meals=False, is_meal_reviewed=True, user=user,
                                            date__gte=start_date)
    meals_count = user_meals.count()
    if days_passed:
        meals_prc = Decimal(meals_count) / Decimal(days_passed) * Decimal(100)
    else:
        meals_prc = 0

    overcalory_meals_count = user_meals.filter(is_overcalory=True).count()
    ok_meals_count = user_meals.filter(is_ooc=0, faults=0).count()
    if ok_meals_count:
        ok_meals_prc = Decimal(ok_meals_count) / Decimal(meals_count) * Decimal(100)
    else:
        ok_meals_prc = 0

    if meals_count:
        overcalory_meals_prc = Decimal(overcalory_meals_count) / Decimal(meals_count) * Decimal(100)
    else:
        overcalory_meals_prc = 0

    steps_filter = DiaryRecord.objects.filter(user=user, steps__isnull=False, date__gte=start_date)
    steps_count = steps_filter.count()
    steps_count_ok = steps_filter.filter(steps__gte=10000).count()
    if steps_count:
        steps_ok_prc = Decimal(steps_count_ok) / Decimal(steps_count) * Decimal(100)
    else:
        steps_ok_prc = 0

    steps_quant = 0.5
    steps_get = math.ceil((steps_count - steps_count_ok) * steps_quant)
    steps_other = None

    if steps_get:
        index = min(steps_get, steps_count - 1)
        steps_other = steps_filter.order_by('steps').all()[index:index + 1].get()
        steps_other = Decimal(steps_other.steps) / 100

    sleep_filter = DiaryRecord.objects.filter(user=user, sleep__isnull=False, date__gte=start_date)
    sleep_count = sleep_filter.count()
    sleep_count_ok = sleep_filter.filter(sleep__gte=8).count()
    if sleep_count:
        sleep_percentage_ok = Decimal(sleep_count_ok) / Decimal(sleep_count) * Decimal(100)
    else:
        sleep_percentage_ok = 0

    start_weight = None
    last_weight = None
    last_bmi = None
    start_bmi = None

    start_diary = DiaryRecord.objects.filter(
        user=user,
        date__gte=start_date,
        weight__isnull=False
    ).order_by('date').first()

    last_diary = DiaryRecord.objects.filter(user=user, weight__isnull=False).order_by('-date').first()

    if start_diary:
        start_weight = start_diary.weight
        if user.profile.height:
            start_bmi = start_weight / ((Decimal(user.profile.height) / 100) ** 2)

    if last_diary:
        last_weight = last_diary.weight
        if user.profile.height:
            last_bmi = last_weight / ((Decimal(user.profile.height) / 100) ** 2)

    month_diary = DiaryRecord.objects.filter(
        user=user,
        date__gte=timezone.now().date() - timedelta(days=30),
        weight__isnull=False
    ).order_by('date').first()

    report.weight_delta_weekly_mon = None

    if month_diary:
        month_weight = month_diary.weight
        month_days_passed = (timezone.now().date() - month_diary.date).days
        month_weeks_passed = math.ceil(month_days_passed / 7.0)
        if month_weeks_passed:
            report.weight_delta_weekly_mon = (last_weight - month_weight) / Decimal(month_weeks_passed)
        else:
            report.weight_delta_weekly_mon = last_weight - month_weight

    report.weight_delta = None
    report.weight_delta_weekly = None

    if start_weight:
        report.weight_delta = last_weight - start_weight
        if weeks_passed:
            report.weight_delta_weekly = report.weight_delta / Decimal(weeks_passed)
        else:
            report.weight_delta_weekly = report.weight_delta

    faults_stat = DiaryMealFault.objects.filter(
        diary_record__user_id=user.pk,
        diary_record__date__gte=start_date,
        fault__is_public=True
    ).values('fault_id') \
        .annotate(
        days_count=Count('diary_record__date', distinct=True),
        faults_count=Count('id', distinct=True),
        title=F('fault__title')
    ).order_by('fault_id')
    faults_stat = list(faults_stat)

    # Get JSON template
    path_to_assets = os.path.join(settings.BASE_DIR, "srbc", "assets", "charts_data")
    path_to_tpl = os.path.join(path_to_assets, 'export_config.json')
    with open(path_to_tpl) as f:
        config_tpl = json.load(f)

    # Get charts data
    diaries = DiaryRecord.objects.filter(
        user_id=user.pk,
        date__lte=(timezone.now().date() + timedelta(days=1))
    )

    series = {
        "weight": [],
        "trueweight": [],
        "steps": [],
        "sleep": [],
        "meals": [],
        "faults": [],
    }

    epoch = datetime.utcfromtimestamp(0)
    faults_count = 0

    for diary in diaries:

        timestamp = (datetime.combine(diary.date, datetime.min.time()) - epoch).total_seconds() * 1000.0
        if diary.weight is not None:
            series['weight'].append([timestamp, float(round(diary.weight, 1))])
        else:
            series['weight'].append([timestamp, None])

        if diary.trueweight is not None:
            series['trueweight'].append([timestamp, float(round(diary.trueweight, 1))])

        if diary.steps is not None:
            series['steps'].append([timestamp, float(round(Decimal(diary.steps) / 10000 * 100, 1))])
        else:
            series['steps'].append([timestamp, None])

        if diary.sleep is not None:
            series['sleep'].append([timestamp, float(round(Decimal(min(diary.sleep, 8.)) / 8 * 100, 1))])
        else:
            series['sleep'].append([timestamp, None])

        if diary.is_ooc:
            # series['meals'].append([timestamp, 0])
            faults_count += 3
            series['faults'].append([timestamp, 3])
        else:
            # if diary.meals:
            #     series['meals'].append([timestamp, diary.meals * 10])
            # else:
            #     series['meals'].append([timestamp, None])

            # series['meals'].append([timestamp, diary.meals])

            if diary.faults:
                series['faults'].append([timestamp, diary.faults])
                faults_count += diary.faults
            else:
                series['faults'].append([timestamp, None])

    # Put charts data to JSON
    config_tpl['series'][0]['data'] = series['weight']
    config_tpl['series'][1]['data'] = series['trueweight']
    # config_tpl['series'][2]['data'] = series['meals']
    config_tpl['series'][3]['data'] = series['faults']
    config_tpl['series'][4]['data'] = series['steps']
    config_tpl['series'][5]['data'] = series['sleep']
    report.chart_data = config_tpl

    tmp_image_name = os.path.join('/tmp', 'srbc_report_%s.png' % report.hashid)

    # Save JSON file to TMP
    with tempfile.NamedTemporaryFile() as temp_file:
        temp_file.write(json.dumps(config_tpl).encode())
        temp_file.flush()
        # Run ChartIMG script
        process = Popen([
            '/home/django/charts/bin/cli.js',
            '-infile', temp_file.name,
            '-outfile', tmp_image_name,
            '-nologo', 'true',
            '-constr', 'Stock',
        ], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

    # Check image exists
    if not os.path.isfile(tmp_image_name):
        return SystemError()

    # Get image
    # Put image to the cloud
    with open(tmp_image_name, 'rb') as fo:
        new_file = File(fo)
        report.chart_image.save('srbc_report_%s.png' % report.hashid, new_file, save=True)

    # Make PDF
    options = {
        'page-size': 'A4',
        'margin-top': '0.4in',
        'margin-right': '0.4in',
        'margin-bottom': '0.4in',
        'margin-left': '0.4in',
        'encoding': "UTF-8",
        'orientation': "Landscape",
        'custom-header': [
            ('Accept-Encoding', 'gzip')
        ],
        'no-outline': None
    }

    # TODO: move pluralizing to template filter

    tpl = loader.get_template('pdf/user_report.html')

    weeks_title = pluralize(weeks_passed, ['неделя', 'недели', 'недель'])
    sleep_count_ok_days_title = pluralize(sleep_count_ok, ['день', 'дня', 'дней'])
    meals_title = pluralize(meals_count, ['день', 'дня', 'дней'])
    meals_overcalory_title = pluralize(overcalory_meals_count, ['день', 'дня', 'дней'])
    steps_title = pluralize(steps_count_ok, ['день', 'дня', 'дней'])

    #     TODO: remove hardcode
    pdf_url = "https://static.selfreboot.camp/reports/%s/%s.pdf" % (
        report.date.strftime('%Y-%m-%d'),
        report.hashid,
    )
    qr = qrcode.make(pdf_url, image_factory=qrcode.image.svg.SvgImage)
    qr_io = io.BytesIO()
    qr.save(qr_io)
    qr_contents = qr_io.getvalue()
    qr_io.close()

    if not report.weight_delta:
        report.weight_delta = 0

    # logger.info(qr_contents)
    content = {
        "start_date": start_date,
        "days_count": days_passed,
        "weeks_passed": weeks_passed,
        "weight_delta_percent_text": ('%.1f%%' % (100 * report.weight_delta / start_weight)) if start_weight else None,
        "bmi_start": start_bmi,
        "bmi_current": last_bmi,
        "meals_count": meals_count,
        "meals_prc": meals_prc,
        "meals_title": meals_title,
        "meals_ok_count": ok_meals_count,
        "meals_ok_prc": ok_meals_prc,
        "meals_overcalory_count": overcalory_meals_count,
        "meals_overcalory_prc": overcalory_meals_prc,
        "meals_overcalory_title": meals_overcalory_title,
        "meals_faults": faults_stat,
        "steps_count": steps_count,
        "steps_ok": steps_count_ok,
        "steps_ok_prc": steps_ok_prc,
        "steps_other_prc": steps_other,
        "steps_title": steps_title,
        "weeks_title": weeks_title,
        "sleep_count": sleep_count,
        "sleep_count_ok": sleep_count_ok,
        "sleep_prc_ok": sleep_percentage_ok,
        "sleep_count_ok_days_title": sleep_count_ok_days_title,
        "faults_count": faults_count,
        "qr": qr_contents.decode(),
        "report": report,
    }
    html = tpl.render(content)

    # Save PDF to the cloud
    pdf = pdfkit.from_string(html, False, options=options)
    report.pdf_file = ContentFile(pdf, "%s.pdf" % report.hashid)
    report.save()


@app.task()
def send_notification(chat_id, content):
    """ Отправляет в чат телеграмма сообщение.

    :param chat_id: номер чата
    :type chat_id: str | int
    :param content:
    :type content: unicode
    """
    try:
        msg = DjangoTelegramBot.dispatcher.bot.send_message(
            chat_id=chat_id,
            text=content,
            disable_web_page_preview=True,
            parse_mode='Markdown',
            timeout=5
        )
        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
    except Exception as e:
        # TODO: в случае ошибки сохранить id сообщения и контент и отправить после починки ошибки?
        logger.exception(e)


@app.task()
@transaction.atomic
def update_diary_trueweight(user_id, start_from=None):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error("[update_diary_trueweight] User not found", extra={'user_id': user_id})
        return

    # Locking
    Profile.objects.select_for_update().get(user=user)

    # start_from - начиная с этой даты нужно сделать пересчет веса
    # найдем первую заполненную дату перед этой датой
    if start_from:
        # дата передается в формате '2016-06-06T00:00:00', поэтому нужно ее перевести в дату
        start_from = datetime.strptime(start_from, "%Y-%m-%dT%H:%M:%S").date()

        # try - catch добавлено специально, last слетает видимо в какой-то версии
        try:
            previous_day = DiaryRecord.objects.filter(
                user=user,
                date__lt=start_from
            ).exclude(
                weight__isnull=True
            ).order_by('date').last()
        except Exception as e:
            previous_day = None

        # отдельно вынесем ситуацию, когда пересчитываем с середины записей и прошлая не перессчитана.
        # делаем вид, что такой записи нет, когда ее будут перессчитывать - тогда и заново зацепим все текущие
        if previous_day and not previous_day.trueweight:
            previous_day = None

        # список записей для пересчета веса
        diaries = DiaryRecord.objects.filter(
            user=user,
            date__gte=start_from
        ).exclude(
            weight__isnull=True
        ).all()

    else:
        # если фгаг не передан, то отрабатывает старая логика
        previous_day = None
        DiaryRecord.objects.filter(user=user).update(trueweight=None)
        diaries = DiaryRecord.objects.filter(user=user).exclude(weight__isnull=True).all()

    ma_coeff = Decimal(2 / (1 + float(settings.TRUEWEIGHT_DELAY)))

    for diary in diaries:
        if previous_day is None:

            if diary.trueweight is None:
                diary.trueweight = diary.weight
                diary.save()

            previous_day = diary
            continue

        days_diff = (diary.date - previous_day.date).days
        power = Decimal(min(1, ma_coeff * days_diff))

        diary.trueweight = power * diary.weight + (1 - power) * previous_day.trueweight
        diary.save()
        previous_day = diary

    return True


@app.task()
def update_collages_image_info(checkpoint_id=None, diary_record_id=None):
    """ Рассчитывает информацию для изображений коллажа (рост, имт, дельту веса, дельту замеров).
    Пересчитываем данные для ВСЕХ изображений, на которые влияет чекпоинт или запись дневника.

    NB: Можно передавать либо checkpoint_id, либо diary_record_id.

    :param checkpoint_id: идентификатор чекпоинта, относительно которого необходимо обновить image_info у изображений
    :type checkpoint_id: int
    :param diary_record_id: идентификатор дневника, относительно которого необходимо обновить image_info у изображений
    :type diary_record_id: int
    """
    assert isinstance(checkpoint_id, int) or isinstance(diary_record_id, int), \
        "Wrong param checkpoint_id [%s] or diary_record_id [%s]" % (checkpoint_id, diary_record_id)
    assert not (isinstance(checkpoint_id, int) and isinstance(diary_record_id, int)), \
        "Expected only checkpoint_id or diary_record_id, got both of them."

    # Изображения фото-ленты, информацию которых необходимо обновить,
    # определяются относительно даты чекпоинта или записи дневника.
    # Так как в обоих случаях алгоритм оданаков,
    # то ниже под "сравниваемый объект" будем понимать объекта класса чекпоинта или записи дневника.

    # === 1) определим относительно какого объекта необходимо обновить данные фото-ленты
    if checkpoint_id:
        cmp_cls = Checkpoint
        cmp_obj_id = checkpoint_id
    else:
        cmp_cls = DiaryRecord
        cmp_obj_id = diary_record_id

    try:
        # объект, относительно которого необходимо обновить данные фото-ленты
        cmp_obj = cmp_cls.objects.get(id=cmp_obj_id)
    except ObjectDoesNotExist:
        if isinstance(cmp_cls, Checkpoint):
            logger.error("[update_collages_image_info] Checkpoint not found", extra={'object_id': cmp_obj_id})
        else:
            logger.error("[update_collages_image_info] DiaryRecord not found", extra={'object_id': cmp_obj_id})
        return

    user_id = cmp_obj.user.pk
    user = User.objects.get(id=user_id)

    # === 2) определим первый сравниваемый объект (чекпоинт или запись дневника) после старта потока
    try:
        _first_cmp_object = cmp_cls.objects.filter(user_id=user_id).only('id').earliest('date')
    except ObjectDoesNotExist:
        # такого не может быть,
        # либо вызвали таск ДО коммита при создании первого сравниваемого объекта (чекпоинта или записи дневника),
        # либо сравниваемый объект УДАЛИЛИ
        logger.error("First compare object not found. Probably race condition detected",
                     extra={'cmp_object_id': cmp_obj_id, 'cmp_cls': str(cmp_cls)})
        return
    else:
        first_cmp_object_id = _first_cmp_object.id

    # === 3) определим объект следующий за cmp_obj по дате
    try:
        _next_cmp_obj = cmp_cls.objects.filter(user_id=user_id, date__gt=cmp_obj.date).only('date').earliest('date')
    except ObjectDoesNotExist:
        next_cmp_obj_date = None
    else:
        next_cmp_obj_date = _next_cmp_obj.date

    # === 4) определим затронутые изображения коллажа
    image_types = ['CHECKPOINT_PHOTO', 'CHECKPOINT_PHOTO_FRONT', 'CHECKPOINT_PHOTO_SIDE', 'CHECKPOINT_PHOTO_REAR']
    query = SRBCImage.objects.filter(user_id=user_id, image_type__in=image_types, date__gte=cmp_obj.date)

    # Если текущий сравниваемый объект - первый после старта потока
    if cmp_obj.id == first_cmp_object_id:
        # изменяем информацию для ВСЕХ изображений коллажа
        affected_images_data = list(query.values('date').annotate(ids=ArrayAgg('id')))
    else:
        # изменяем информацию для фотографий коллажа, дата которых - близжайщая к дате текущего сравниваемого объекта
        if next_cmp_obj_date:
            # Фотографий, image_info которых основывается на основании сравниваемого объекта
            # (чекпоинте или на дневнике питания) может быть несколько (имеется в виду за разные дни).
            # В связи с этим, добавляем фильтр.
            query.filter(date__lt=next_cmp_obj_date)
        try:
            affected_images_data = list(query.values('date').annotate(ids=ArrayAgg('id')))
        except ObjectDoesNotExist:
            logger.error('[tasks.update_collages_image_info] Unexpected ObjectDoesNotExist',
                         extra={'cmp_object_id': cmp_obj_id, 'cmp_cls': str(cmp_cls)})
            affected_images_data = []

    # Получим данные сгрупированные по дню дабы зря не подсчитывать image_info для фотографий одного дня.
    # affected_images_data имеет вид [{'date': datetime.date(2018, 6, 10), 'ids': [51, 52, 53]}, ...]

    # === 5) посчитаем новые данные замеров для всех затронутых изображений
    for image_data in affected_images_data:
        image_info = collect_image_info(user=user, date=image_data['date'])
        SRBCImage.objects.filter(pk__in=image_data['ids']).update(image_info=image_info)


@app.task(autoretry_for=(IOError,),
          retry_kwargs={'max_retries': 3},
          default_retry_delay=30)  # секунды
def create_or_update_data_image(user_id, diary_record_id):

    assert isinstance(user_id, int) and isinstance(diary_record_id, int), \
        "Expected user_id and diary_record_id."

    try:
        user = User.objects.get(id=user_id)
        diary = DiaryRecord.objects.get(pk=diary_record_id)
    except User.DoesNotExist:
        logger.error("[update_diary_trueweight] User not found", extra={'user_id': user_id})
        return
    except DiaryRecord.DoesNotExist:
        logger.error("[update_diary_trueweight] DiaryRecord not found", extra={'user_id': diary_record_id})
        return

    filename = str(uuid.uuid4())

    original_image = generate_data_image(user, diary.date)
    original_image.resize((1200, 1200), Image.ANTIALIAS)

    image_file = put_image_in_memory(original_image, filename=filename)

    thumbnail = original_image.resize((400, 400), Image.ANTIALIAS)
    thumbnail_file = put_image_in_memory(thumbnail, filename="tn_%s" % filename)

    srbc_image = save_image(
        user=user,
        date=diary.date,
        image_type='DATA',
        image_file=image_file,
        thumbnail_file=thumbnail_file
    )

    # === формируем текст описания коллажа с данными
    tz = pytz.timezone(user.profile.timezone)
    diary_date_datetime = datetime.combine(diary.date, datetime.min.time())
    yesterday = tz.localize(diary_date_datetime) - timedelta(days=1)

    if yesterday.month == diary.date.month:
        d_text = '%02d-%s' % (yesterday.day, dateformat.format(diary.date, 'd E'))
    else:
        d_text = '%s-%s' % (
            dateformat.format(yesterday, 'd E'), dateformat.format(diary.date, 'd E')
        )

    weight_delta_yesterday, weight_delta_start = diary.get_delta_weights

    if weight_delta_start and weight_delta_yesterday:
        weight_text = 'Вес: %+g / %+.1f' % (weight_delta_yesterday, weight_delta_start)
    else:
        weight_text = 'Вес: Нет данных'

    hashtags_texts = ['#selfrebootcampданные #selfrebootcamp']
    if user.profile.is_perfect_weight:
        hashtags_texts.append('#selfrebootcampидеальныйвес')
    if user.profile.is_in_club:
        hashtags_texts.append('#selfrebootcampклуб')
    if user.profile.is_pregnant:
        hashtags_texts.append('#selfrebootcampособыйслучай')
    h_text = ' '.join(hashtags_texts)

    if user.profile.wave:
        start_text = 'Старт: %s' % user.profile.wave.start_date.strftime('%d.%m.%Y')
        srbc_image.image_info = '\n'.join([d_text, weight_text, start_text, h_text])
    else:
        srbc_image.image_info = '\n'.join([d_text, weight_text, h_text])

    srbc_image.save(update_fields=['image_info', 'meta_data', ])


# FIXME пока уберем @app.task(bind=True) - при использовании надо self первым параметром
@app.task(autoretry_for=(IOError,),
          retry_kwargs={'max_retries': 3},
          default_retry_delay=30)  # секунды
def collage_build(user_id, photoset_id):

    assert isinstance(user_id, int) and isinstance(photoset_id, int), \
        "Expected user_id and photoset_id."

    # FIXME пока уберем try-except, будем смотреть celery
    # если все устроит - потом удалить закоменченный код

    # Много вложенных рассчетов и функций, сделаем общий try/except
    # try:
    user = User.objects.get(id=user_id)
    photoset = CheckpointPhotos.objects.get(pk=photoset_id)
    photoset_base = CheckpointPhotos.objects.filter(user_id=user_id, status='APPROVED').order_by('date').first()

    # проверим, что photoset_base найден, иначе свалится непонятная ошибка
    if not photoset_base:
        raise Exception('Нет аппрувнутых фотографий')

    if photoset_base.id == photoset_id:
        result = build_3view_collage(photoset)
    else:
        result = build_compare_collages(photoset_base, photoset)

    image_info = collect_image_info(user=user, date=photoset.date)
    for srbc_image in result:
        srbc_image.image_info = image_info
        srbc_image.save(update_fields=['image_info'])

    return get_checkpoint_photo_set(user_id)

    # except Exception as e:
    #     logger.error('[tasks.collage_build] %s', str(e))
    #     self.update_state(
    #         state=states.FAILURE,
    #         meta=e
    #     )

    #     # ignore the task so no other state is recorded
    #     raise Ignore()


@app.task(autoretry_for=(IOError,),
          retry_kwargs={'max_retries': 3},
          default_retry_delay=30)  # секунды
def create_meal_collage(diary_id):
    diary = DiaryRecord.objects.get(pk=diary_id)

    diary.meal_image = _create_meal_collage(diary)
    
    # === формируем текст рациона
    if diary.meal_image:
        text_date = diary.date - timedelta(days=1)
        text_date = dateformat.format(text_date, 'd E')

        wake_up_text = 'Подъём – %s' % diary.wake_up_time.strftime("%H:%M")
        meal_texts = []
        for meal in DiaryMeal.objects.filter(diary=diary).order_by('start_time_is_next_day', 'start_time'):
            if meal.is_meal:
                components_text = get_meal_components_text(meal)

                dt = meal.start_time.strftime("%H:%M")
                if meal.start_time_is_next_day:
                    dt = '%s (%s)' % (dt, 'после полуночи')
                meal_texts.append('%s – %s' % (dt, components_text))

            elif meal.meal_type == DiaryMeal.MEAL_TYPE_SLEEP:
                st_text = '%s' % meal.start_time.strftime("%H:%M")
                et_text = '%s' % meal.end_time.strftime("%H:%M")

                if meal.start_time_is_next_day:
                    st_text += ' (после полуночи)'
                if meal.end_time_is_next_day:
                    et_text += ' (после полуночи)'

                meal_texts.append('%s-%s – %s' % (st_text, et_text, 'Дневной сон'))

            elif meal.meal_type == DiaryMeal.MEAL_TYPE_HUNGER:
                dt = meal.start_time.strftime("%H:%M")
                meal_texts.append('%s – %s. Интенсивность %s' % (dt, 'Чувство голода', meal.hunger_intensity))
            else:
                dt = meal.start_time.strftime("%H:%M")
                meal_texts.append('%s – %s. %s %s' % (dt, 'Замер уровня глюкозы в крови',
                                  meal.glucose_level, meal.glucose_unit))

        meals_text = '\n'.join(meal_texts)

        dt = diary.bed_time.strftime("%H:%M")
        if diary.bed_time_is_next_day:
            dt = '%s (%s)' % (dt, 'после полуночи')
        bed_time_text = 'Отбой – %s' % dt

        if diary.water_consumed:
            water_text = 'Воды за день – %s л' % (round(diary.water_consumed * 10) / 10)
        else:
            water_text = 'Воды за день – 0 л'

        hashtag_text = '#selfrebootcamp #selfrebootcampеда %s' % diary.meal_hashtag

        diary.meal_image.image_info = '\n'.join(
            (text_date, wake_up_text, meals_text, bed_time_text, water_text, hashtag_text)
        )

        if diary.has_sugar:
            diary.meal_image.meta_data['has_sugar'] = True

        if diary.has_alco:
            diary.meal_image.meta_data['has_alco'] = True

        diary.meal_image.is_published = True
        diary.meal_image.save(update_fields=['image_info', 'is_published', 'meta_data'])

    diary.save()
