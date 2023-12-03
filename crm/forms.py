# -*- coding: utf-8 -*-
from django import forms
from crm.models import UserAdmissionTestQuestion, UserAdmissionTest


class AdmissionTestAskQuestionForm(forms.ModelForm):
    class Meta:
        model = UserAdmissionTest
        fields = [
            'question_asked'
        ]
        labels = {
            'question_asked': ''
        }


class AdmissionTestRecommendationForm(forms.ModelForm):
    class Meta:
        model = UserAdmissionTest
        fields = [
            'recommendation_info'
        ]
        labels = {
            'recommendation_info': ''
        }


class AdmissionTestQuestionForm(forms.ModelForm):
    class Meta:
        model = UserAdmissionTestQuestion
        fields = [
            'answer_ok',
            'answer_ok_comment',
            'answer_interval',
            'answer_interval_comment',
            'answer_sweet',
            'answer_sweet_comment',
            'answer_protein',
            'answer_protein_comment',
            'answer_fat',
            'answer_fat_comment',
            'answer_carb',
            'answer_carb_comment',
            'answer_weight',
            'answer_weight_comment',
        ]
        widgets = {

        }

        labels = {
            'answer_ok': "Рацион полностью соответствует методичке",
            'answer_ok_comment': "Поясните ваш выбор",
            'answer_interval': "В рационе превышены промежутки между приемами пищи",
            'answer_interval_comment': "Поясните ваш выбор",
            'answer_sweet': "В рационе присутствует ошибка \"сладкое натощак\"? "
                            "Натощак для сладкого – простых (быстрых) углеводов – "
                            "это более двух часов после предыдущего приема пищи",
            'answer_sweet_comment': "Поясните ваш выбор",
            'answer_protein': "В рационе есть приемы пищи с недобором белка",
            'answer_protein_comment': "Поясните ваш выбор",
            'answer_fat': "В рационе есть превышение жирности пищи",
            'answer_fat_comment': "Поясните ваш выбор",
            'answer_carb': "В рационе превышено или уменьшено по сравнению со схемой количество углеводов",
            'answer_carb_comment': "Поясните ваш выбор",
            'answer_weight': "В рационе неверно взвешены порции (в проекте мы называем их \"неверные навески\")",
            'answer_weight_comment': "Поясните ваш выбор",
        }
