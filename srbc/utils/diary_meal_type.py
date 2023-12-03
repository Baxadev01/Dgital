from srbc.models import DiaryMeal

DIARY_MEAL_TIMETABLE = [
    {'start': '00:00', 'end': '04:59', 'is_next_day': False, 'type': DiaryMeal.MEAL_TYPE_SNACK},
    {'start': '05:00', 'end': '06:59', 'is_next_day': False, 'type': DiaryMeal.MEAL_TYPE_PREBREAKFAST},
    {'start': '07:00', 'end': '09:59', 'is_next_day': False, 'type': DiaryMeal.MEAL_TYPE_BREAKFAST},
    {'start': '10:00', 'end': '12:29', 'is_next_day': False, 'type': DiaryMeal.MEAL_TYPE_BRUNCH},
    {'start': '12:30', 'end': '15:14', 'is_next_day': False, 'type': DiaryMeal.MEAL_TYPE_LUNCH},
    {'start': '15:15', 'end': '16:44', 'is_next_day': False, 'type': DiaryMeal.MEAL_TYPE_MERIENDA},
    {'start': '16:30', 'end': '18:59', 'is_next_day': False, 'type': DiaryMeal.MEAL_TYPE_DINNER},
    {'start': '19:00', 'end': '23:59', 'is_next_day': False, 'type': DiaryMeal.MEAL_TYPE_SNACK},
    {'start': '00:00', 'end': '23:59', 'is_next_day': True, 'type': DiaryMeal.MEAL_TYPE_SNACK},
]


def get_diary_meal_timetable(diary):
    # задел на будущее, раз их будет несколько вариантов,
    # пока возвращаем единственный
    return DIARY_MEAL_TIMETABLE


def update_meal_types(diary):
    # в зависимости от "расписания" обновляет типы приемов пищи
    diary_timetable = get_diary_meal_timetable(diary)

    meals_data = diary.meals_data.all()

    for meal in meals_data:
        if not meal.is_meal:
            # если не прием пищи, то пропускаем
            continue

        meal_time = meal.start_time.strftime('%H:%M')

        new_type = next((item['type'] for item in diary_timetable
                         if item['end'] >= meal_time >= item['start']
                         and item['is_next_day'] == meal.start_time_is_next_day), None)

        if new_type and new_type != meal.meal_type:
            meal.meal_type = new_type
            meal.save(update_fields=['meal_type'])
