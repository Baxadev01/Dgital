# -*- coding: utf-8 -*-
from django import forms
from support.models import Ticket
from captcha.fields import ReCaptchaField


class TicketForm(forms.ModelForm):
    captcha = ReCaptchaField(label="Проверка на человечность")

    class Meta:
        model = Ticket
        fields = [
            'full_name', 'email', 'subject', 'body',
        ]

        widgets = {
            'subject': forms.TextInput,
        }
        labels = {
            'full_name': "Представьтесь, пожалуйста, полностью",
            'email': "Ваша электронная почта",
            'subject': "Тема сообщения",
            'body': "Текст сообщения",
            'captcha': "Проверка на человечность",
        }
