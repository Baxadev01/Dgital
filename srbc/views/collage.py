# -*- coding: utf-8 -*-
import os
from datetime import datetime, timedelta, date

from PIL import Image, ImageFont, ImageDraw
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from srbc.decorators import validate_user, has_desktop_access
from srbc.models import DiaryRecord


@login_required
@has_desktop_access
@validate_user
def data_collage_page(request, data_date=None):
    """ Возвращает данные для страницы коллажа.
    
    :param request:
    :type request: django.core.handlers.wsgi.WSGIRequest
    :param data_date: день для выбора данных коллажа
    :type data_date: str    
    """
    if not data_date:
        today_str = datetime.now().strftime("%Y-%m-%d")
        return redirect('/diary/%s/data/collage/' % today_str)

    today = datetime.strptime(data_date, "%Y-%m-%d")
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    if tomorrow.date() > date.today():
        tomorrow = None

    diary_today = DiaryRecord.objects.filter(user=request.user, date=today.date()).first()
    if diary_today:
        weight_delta_yesterday, weight_delta_start = diary_today.get_delta_weights
    else:
        weight_delta_yesterday, weight_delta_start = None, None

    return render(
        request,
        'srbc/collage_data_message.html',
        {
            'today': today,
            'yesterday': yesterday,
            'tomorrow': tomorrow,
            'weight_delta_yesterday': weight_delta_yesterday,
            'weight_delta_start': weight_delta_start,
            # 'collage_description': collage_description,
        }
    )


@login_required
@has_desktop_access
@validate_user
def data_collage_gen(request, data_date):
    today = datetime.strptime(data_date, "%Y-%m-%d").date()
    image = generate_data_image(request.user, today)
    response = HttpResponse(content_type="image/jpeg")
    image.save(response, format='JPEG', subsampling=0, quality=90)

    return response


def generate_data_image(user, work_date):
    yesterday = work_date - timedelta(days=1)

    steps_count = None
    sleep_duration = None
    weight = None
    meals_score = None
    meals_faults = None
    meals_overcalory = False

    today_str = work_date.strftime('%d.%m.%Y')
    yesterday_str = yesterday.strftime('%d.%m.%Y')

    diary = DiaryRecord.objects.filter(user=user, date=work_date).first()
    if diary:
        steps_count = diary.steps
        sleep_duration = diary.sleep
        weight = diary.weight
        meals_score = diary.meals
        meals_faults = diary.faults
        meals_overcalory = '*' if diary.is_overcalory else ''

    path_to_assets = os.path.join(settings.BASE_DIR, "srbc", "assets", "collage_data")
    path_to_template = os.path.join(path_to_assets, "srbc_data_template.jpg")
    path_to_meal_template = os.path.join(path_to_assets, "srbc_data_template_meal.jpg")

    path_to_font = os.path.join(path_to_assets, "days.ttf")
    offset_y = 1.3
    img_template = Image.open(path_to_template)
    img_font_240 = ImageFont.truetype(path_to_font, 240)
    img_font_200 = ImageFont.truetype(path_to_font, 200)
    img_font_160 = ImageFont.truetype(path_to_font, 160)
    img_font_150 = ImageFont.truetype(path_to_font, 150)
    img_font_96 = ImageFont.truetype(path_to_font, 96)

    if user.profile.is_self_meal_formula:
        img_over = Image.open(path_to_meal_template, 'r')
        img_template.paste(img_over, (1, 450))

    steps_count_formatted = "{:,}".format(steps_count) if steps_count else "--,---"
    # steps_count_formatted = steps_count_formatted.replace(",", u"\u202f")

    if meals_score is not None and meals_faults is not None:
        meals_formula_text = "%d/%d%s" % (meals_score, meals_faults, meals_overcalory)
    else:
        meals_formula_text = "N/A"

    if sleep_duration:
        sleep_duration_minutes = int(5 * round(float(sleep_duration * 60) / 5))
        sleep_duration_hours = sleep_duration_minutes / 60
        sleep_duration_minutes = sleep_duration_minutes - sleep_duration_hours * 60
        sleep_duration_text = "%d:%02d" % (sleep_duration_hours, sleep_duration_minutes)
    else:
        sleep_duration_text = "--:--"

    if weight:
        weight_text = '{0:.1f}'.format(weight)
        weight_suffix = " кг"
    else:
        weight_text = "--.-"
        weight_suffix = " кг"

    template_draw = ImageDraw.Draw(img_template)
    font_color = (255, 255, 255)

    start_date_dimensions = template_draw.textsize(yesterday_str, img_font_96)
    end_date_dimensions = template_draw.textsize(today_str, img_font_96)
    steps_dimensions = template_draw.textsize(steps_count_formatted, img_font_200)

    weight_dimension = template_draw.textsize(weight_text, img_font_240)
    weight_postfix_dimension = template_draw.textsize(weight_suffix, img_font_160)

    x = (600 - start_date_dimensions[0]) / 2
    y = (150 - start_date_dimensions[1] * offset_y) / 2
    template_draw.text(xy=(x, y), text=yesterday_str, fill=font_color, font=img_font_96)
    x = 600 + (600 - end_date_dimensions[0]) / 2
    y = 1050 + (150 - end_date_dimensions[1] * offset_y) / 2
    template_draw.text(xy=(x, y), text=today_str, fill=font_color, font=img_font_96)
    x = (400 + (800 - steps_dimensions[0]) / 2) if steps_dimensions[0] < 770 else (1170 - steps_dimensions[0])
    y = 150 + (300 - steps_dimensions[1] * offset_y) / 2
    template_draw.text(xy=(x, y), text=steps_count_formatted, fill=font_color, font=img_font_200)

    if user.profile.is_self_meal_formula:
        sleep_dimensions = template_draw.textsize(sleep_duration_text, img_font_150)
        meals_dimensions = template_draw.textsize(meals_formula_text, img_font_150)

        x = 740 + (460 - sleep_dimensions[0]) / 2
        y = 450 + (300 - sleep_dimensions[1] * offset_y) / 2
        template_draw.text(xy=(x, y), text=sleep_duration_text, fill=font_color, font=img_font_150)

        x = 140 + (460 - meals_dimensions[0]) / 2
        y = 450 + (300 - meals_dimensions[1] * offset_y) / 2
        template_draw.text(xy=(x, y), text=meals_formula_text, fill=font_color, font=img_font_150)
    else:
        sleep_dimensions = template_draw.textsize(sleep_duration_text, img_font_200)
        x = 400 + (800 - sleep_dimensions[0]) / 2
        y = 440 + (300 - sleep_dimensions[1] * offset_y) / 2
        template_draw.text(xy=(x, y), text=sleep_duration_text, fill=font_color, font=img_font_200)

    x = (1200 - (weight_dimension[0] + weight_postfix_dimension[0])) / 2
    y = 750 + (300 - weight_dimension[1] * offset_y) / 2
    template_draw.text(xy=(x, y), text=weight_text, fill=font_color, font=img_font_240)
    x = (1200 - (weight_dimension[0] + weight_postfix_dimension[0])) / 2 + weight_dimension[0]
    y = 750 + (300 - weight_dimension[1] * offset_y) / 2 + weight_dimension[1] - weight_postfix_dimension[1]
    template_draw.text(xy=(x, y), text=weight_suffix, fill=font_color, font=img_font_160)

    return img_template
