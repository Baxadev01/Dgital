RECOMMENDATION_FAULTS = {
    'add_fat': {"faults": ['add_fat'], 'title': 'Добавить жиров'},
    'adjust_calories': {"faults": [], 'title': 'Корректировка калорийности рациона'},
    'adjust_carb_bread_late': {"faults": ['adjust_carb_bread_late'], 'title': 'Убрать полисахариды из ужина'},
    'adjust_carb_bread_min': {"faults": ['adjust_carb_bread_min'], 'title': 'Уменьшение полисахаридов'},
    'adjust_carb_carb_vegs': {"faults": ['adjust_carb_carb_vegs_carbveg', 'adjust_carb_carb_vegs_carb'],
                              'title': 'Исключить запасающие овощи после обеда'},
    'adjust_fruits': {"faults": ['adjust_fruits_sugar'], 'title': 'Простые сахара'},
    'adjust_protein': {"faults": ['adjust_protein'], 'title': 'Корректировка белка в рационе'},
    'adjust_carb_sub_breakfast': {"faults": ['adjust_carb_sub_breakfast'], 'title': 'Замена длинных углеводов на овощи(завтрак посхеме обеда)'},
    'exclude_lactose': {"faults": ['exclude_lactose'], 'title': 'Исключить лактозу'},
    'restrict_lactose_casein': {"faults": ['restrict_lactose_casein'], 'title': 'Ограничить казеин и лактозу'},
    'adjust_carb_mix_vegs': {"faults": ['adjust_carb_mix_vegs'], 'title': 'Смешивать овощи'}
}


FAULT_TITLE = {
    'add_fat': 'нехватка жиров',
    'adjust_carb_bread_late': 'полисахариды - убрать полисахариды из ужина',
    'adjust_carb_bread_min': 'полисахариды - уменьшение полисахаридов',
    'adjust_carb_carb_vegs_carbveg': 'полисахариды в овощах после обеда',
    'adjust_carb_carb_vegs_carb': 'общие полисахариды, включая овощи, после обеда',
    'adjust_fruits_sugar': 'ограничение сахара',
    'adjust_protein': 'белок',
    'adjust_carb_sub_breakfast': 'завтрак по схеме обеда',
    'exclude_lactose': 'убрать лактозу',
    'restrict_lactose_casein': 'убрать казеин',
    'adjust_carb_mix_vegs': 'смешивание овощей',
}


def get_faults_choices(note):

    def add_faults_to_list(fault_list, recommendation):
        faults = RECOMMENDATION_FAULTS[recommendation].get('faults', [])
        for fault in faults:
            fault_list.append(
                {
                    "fault": fault,
                    "title": FAULT_TITLE[fault]
                }
            )

        return fault_list

    fault_list = []

    if not note:
        return fault_list
        
    if note.adjust_calories:
        fault_list = add_faults_to_list(fault_list, 'adjust_calories')

    if note.adjust_protein:
        fault_list = add_faults_to_list(fault_list, 'adjust_protein')

    if note.add_fat:
        fault_list = add_faults_to_list(fault_list, 'add_fat')

    if note.adjust_fruits != 'NO':
        fault_list = add_faults_to_list(fault_list, 'adjust_fruits')

    if note.adjust_carb_mix_vegs:
        fault_list = add_faults_to_list(fault_list, 'adjust_carb_mix_vegs')

    if note.adjust_carb_bread_min:
        fault_list = add_faults_to_list(fault_list, 'adjust_carb_bread_min')

    if note.adjust_carb_bread_late:
        fault_list = add_faults_to_list(fault_list, 'adjust_carb_bread_late')

    if note.adjust_carb_carb_vegs:
        fault_list = add_faults_to_list(fault_list, 'adjust_carb_carb_vegs')

    if note.adjust_carb_sub_breakfast:
        fault_list = add_faults_to_list(fault_list, 'adjust_carb_sub_breakfast')

    if note.exclude_lactose:
        fault_list = add_faults_to_list(fault_list, 'exclude_lactose')

    if note.restrict_lactose_casein:
        fault_list = add_faults_to_list(fault_list, 'restrict_lactose_casein')

    return fault_list


def get_recommendations(faults):
    result = []

    # может быть None
    if faults:
        for fault in faults:
            rec = next((item for item in RECOMMENDATION_FAULTS if fault in RECOMMENDATION_FAULTS[item]['faults']), None)
            if rec:
                result.append(RECOMMENDATION_FAULTS[rec]['title'])

    # небольшой "костыль" из-за того, что для одной рекомендации заложены несколько фолтов.
    result = set(result)
    return result
