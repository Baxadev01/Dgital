# -*- coding: utf-8 -*-
import datetime
import re

from dal import autocomplete
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.formfields import PhoneNumberField

from crm.models import Application
from crm.models import Campaign
from crm.models import DiscountCode
from srbc.models import Invitation, Profile, User, MealProductModeration, MealProduct, Tariff, Wave
from srbc.social import get_ig_user_data


class InstagramForm(forms.Form):
    instagram = forms.CharField(label='Инстаграм-акканунт (ТОЛЬКО НИК-НЕЙМ!!!)', max_length=50, required=True)
    is_private_confirmed = forms.BooleanField(
        label='Я согласен оплатить участие по повышенному тарифу (х2) '
              'с возможностью вести инстаграм-аккаунт для проекта под замком',
        required=False
    )
    is_followers_confirmed = forms.BooleanField(
        label='Я осведомлен, что использование "засвеченного" инстаграмма категорически не рекомендуется '
              'организаторами во избежание вмешательства посторонних лиц в мою личную жизнь',
        required=False
    )

    def clean_instagram(self):
        value = self.cleaned_data.get('instagram')
        if not len(value):
            self.add_error('instagram',
                           'Нужно ввести название вашего Instagram-аккаунта, '
                           'созданного специально для участия в проекте')
        if ':' in value or '/' in value:
            self.add_error('instagram', 'Не нужно вводить всю ссылку. Только ник-нейм.')

        # проверим валидность переданного ник-нейма
        user_data = get_ig_user_data(username=value)

        if user_data is None:
            self.add_error('instagram', 'Нужно ввести существующий ник-нейм.')
        elif user_data.get('is_private'):
            self.add_error('instagram', 'При участии по тарифу "Промо" инстаграм должен быть открытым.')

        return value

    def clean_is_followers_confirmed(self):
        checked = self.cleaned_data.get('is_followers_confirmed')
        if not checked and (
                'linked_account_followers' in self.request.GET or 'linked_account_media' in self.request.GET):
            self.add_error('is_followers_confirmed', '')

        return checked

    def clean_is_private_confirmed(self):
        checked = self.cleaned_data.get('is_private_confirmed')
        if not checked and 'linked_account_private' in self.request.GET:
            self.add_error('is_private_confirmed', '')

        return checked

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(InstagramForm, self).__init__(*args, **kwargs)


class InviteForm(forms.Form):
    code = forms.CharField(label='Персональный код', max_length=25, required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(InviteForm, self).__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data.get('code')
        try:
            invite = Invitation.objects.get(code=code)
        except ObjectDoesNotExist:
            raise forms.ValidationError('Введён неверный код. Попробуйте еще раз или свяжитесь с координатором')

        if invite.expiring_at and invite.expiring_at < datetime.datetime.now():
            raise forms.ValidationError(
                'Введённый код истёк. Обратитесь к координатору для получения нового кода'
            )

        if invite.is_applied:
            raise forms.ValidationError(
                'Введённый код уже был использован. Обратитесь к координатору.'
            )

        if not self.user.profile:
            raise forms.ValidationError(
                'Ошибка регистрации промокода. Обратитесь к координатору.'
            )

        if not invite.wave and not self.user.profile.wave:
            raise forms.ValidationError(
                'Введённый код может быть использован только для продления участия'
            )

        if not invite.wave and not self.user.profile.valid_until:
            raise forms.ValidationError(
                'Введённый код может быть использован только для продления участия'
            )

        if invite.club_only and not self.user.profile.is_in_club:
            raise forms.ValidationError(
                'Введённый код может быть использован только для продления участия в клубе'
            )

        return code


class DiscountForm(forms.Form):
    code = forms.CharField(label='Код на скидку', max_length=21, required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(DiscountForm, self).__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data.get('code')

        if len(code) == 0:
            return code

        try:
            discount = DiscountCode.objects.get(code=code)
        except ObjectDoesNotExist:
            raise forms.ValidationError('Введён неверный код. Попробуйте еще раз или свяжитесь с координатором')

        if discount.expiring_at and discount.expiring_at < datetime.datetime.now():
            raise forms.ValidationError(
                'Введённый код истёк. Обратитесь к координатору для получения нового кода'
            )

        if discount.is_applied:
            raise forms.ValidationError(
                'Введённый код уже был использован. Обратитесь к координатору.'
            )

        if not self.user.profile:
            raise forms.ValidationError(
                'Ошибка регистрации промокода. Обратитесь к координатору.'
            )

        if discount.payment_type != 'CLUB' and self.user.profile.communication_mode != discount.payment_type:
            raise forms.ValidationError(
                'Введённый код не соответствует выбранному формату участия в программе'
            )

        if discount.payment_type == 'CLUB' and not self.user.profile.is_in_club:
            raise forms.ValidationError(
                'Введённый код может быть использован только для скидки на участие в клубе'
            )

        return code


class UserSettingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)
        if self.instance.telegram_id:
            self.fields['mobile_number'].widget.attrs['readonly'] = True
        else:
            self.fields['mobile_number'].required = True

    def clean_mobile_number(self):
        phone_number = self.cleaned_data['mobile_number']
        if self.instance.telegram_id:
            phone_number = self.instance.mobile_number
        else:
            non_decimal = re.compile(r'[^\d]+')
            phone_number = non_decimal.sub('', phone_number)

            phone_number = phone_number.lstrip('0')
            if len(phone_number) < 10:
                raise forms.ValidationError(
                    'Неверный номер телефона. '
                    'Укажите номер мобильного телефона вместе с кодом страны'
                )

            if len(phone_number) == 10 and phone_number[0] == '9':
                phone_number = '7%s' % phone_number

            if len(phone_number) == 11 and phone_number[0] == '8':
                phone_number = '7%s' % phone_number[1:]

            return phone_number

        return phone_number

    class Meta:
        model = Profile
        fields = [
            'timezone',
            'tracker_brand',
            'mobile_number',
            'goal_weight',
            'display_goal_weight',
        ]
        widgets = {

        }

        labels = {
            'goal_weight': "Целевой вес (в кг)",
            'display_goal_weight': "Отображать линию целевого веса на графике",
            'timezone': "Часовой пояс",
            'tracker_brand': "Фитнес-браслет",
            'mobile_number': "Номер телефона (Telegram)",
        }


class PhoneForm(forms.ModelForm):
    phone = PhoneNumberField(
        label="Номер мобильного телефона, к которому привязан аккаунт в Telegram (c кодом страны)",
        widget=forms.TextInput(attrs={'placeholder': '+79876543210'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(PhoneForm, self).__init__(*args, **kwargs)

        if self.user and self.user.profile.telegram_id:
            self.fields['phone'].widget.attrs['readonly'] = True
        else:
            self.fields['phone'].required = True

    def clean_phone(self):
        instance = getattr(self, 'instance', None)
        if self.user and self.user.profile.telegram_id:
            return instance.phone

        phone_number = self.cleaned_data['phone']

        non_decimal = re.compile(r'[^\d]+')

        phone_number = non_decimal.sub('', str(phone_number))

        phone_number = phone_number.lstrip('0')
        if len(phone_number) < 10:
            raise forms.ValidationError(
                'Неверный номер телефона. '
                'Укажите номер мобильного телефона вместе с кодом страны'
            )

        if len(phone_number) == 10 and phone_number[0] == '9':
            phone_number = '7%s' % phone_number

        if len(phone_number) == 11 and phone_number[0] == '8':
            phone_number = '7%s' % phone_number[1:]

        already_profile = Profile.objects.filter(mobile_number=phone_number).exclude(user_id=self.user.pk).exists()
        already_app = Application.objects.filter(phone=phone_number).exclude(pk=self.user.application.pk).exists()

        if already_app or already_profile:
            raise forms.ValidationError(
                'Данный номер телефона уже используется другим участником. '
                'Пожалуйста, используйте что-то более оригинальное.'
            )

        return phone_number

    class Meta:
        model = Application
        fields = [
            'phone',
        ]


class ApplicationForm(forms.ModelForm):
    birth_year = forms.IntegerField(min_value=1917, max_value=2017, required=True, label="Год рождения")
    country = CountryField().formfield(label="Страна")
    goal_weight = forms.DecimalField(min_value=40, max_value=200, required=True, label="Целевой вес")
    weight = forms.DecimalField(min_value=40, max_value=200, required=True, label="Ваш текущий (стартовый) вес, в кг")
    baby_birthdate = forms.DateField(
        input_formats=['%d.%m.%Y'],
        widget=forms.DateInput(
            format='%d.%m.%Y',
            attrs={
                'id': 'baby_birthdate_datepicker',
            }
        ),
        required=False
    )

    # baby_case = forms.ChoiceField(empty_label=None)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ApplicationForm, self).__init__(*args, **kwargs)

    def clean_gender(self):
        gender = self.cleaned_data['gender']

        if gender == 'M':
            self.cleaned_data['baby_case'] = 'NONE'
            self.cleaned_data['baby_birthdate'] = None

        return gender

    def clean_baby_case(self):
        gender = self.cleaned_data.get('gender', None)
        if gender and gender == 'M':
            return 'NONE'
        else:
            return self.cleaned_data['baby_case']

    def clean_baby_birthdate(self):
        gender = self.cleaned_data.get('gender', None)

        if gender and gender == 'M':
            self.cleaned_data['baby_birthdate'] = None
        else:
            if self.cleaned_data['baby_case'] == 'NONE':
                self.cleaned_data['baby_birthdate'] = None
            else:
                if not self.cleaned_data.get('baby_birthdate', None):
                    self.add_error('baby_birthdate', 'Пожалуйста, укажите дату')

        return self.cleaned_data.get('baby_birthdate', None)

    class Meta:
        model = Application
        fields = [
            'gender', 'first_name', 'last_name',
            'country', 'city',
            'height', 'weight', 'birth_year', 'sickness',
            'baby_case',
            'baby_birthdate',
            'goal_weight', 'goals',
        ]
        widgets = {
            'gender': forms.RadioSelect,
            'sickness': forms.Textarea(attrs={'rows': 3}),
            'goals': forms.Textarea(attrs={'rows': 3}),
            'country': forms.TypedChoiceField(),
        }

        labels = {
            'goals': "Другие цели вашего участия в проекте",
        }


class EmailForm(forms.Form):
    first_name = forms.CharField(label="Имя", required=True)
    last_name = forms.CharField(label="Фамилия", required=True)
    email = forms.EmailField(label="Электронная почта", required=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(EmailForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']

        if not email:
            raise forms.ValidationError(
                'Неверный адрес электронной почты. '
            )

        already_user = User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists()
        already_app = Application.objects.filter(email__iexact=email).exclude(pk=self.user.application.pk).exists()

        if already_app or already_user:
            raise forms.ValidationError(
                'Данный адрес электронной почты уже используется другим участником.'
                ' Пожалуйста, используйте что-то более оригинальное.'
            )

        return email


class RealNameForm(forms.Form):
    first_name = forms.CharField(label="Имя", required=True)
    last_name = forms.CharField(label="Фамилия", required=True)


class UsernameForm(forms.Form):
    _username_regex = r'^(?!.*[._]{2}.*)[A-Za-z0-9][A-Za-z0-9_.]{3,14}[A-Za-z0-9]$'
    _regex_error_msg = mark_safe('Имя пользователя должно удовлетворять следующим правилам:<br>\n'
                                 '1) допускаются латинские буквы, цифры, символы: "_", "."<br>\n'
                                 '2) имя пользователя должно быть не короче 5 и не длиннее 16 символов<br>\n'
                                 '3) не должно быть двух символов "_" и/или "." подряд<br>\n'
                                 '4) "_" и "." не могут быть первым или последним символом')
    username = forms.RegexField(label="Имя пользователя", regex=_username_regex, required=True,
                                error_messages={'invalid': _regex_error_msg})

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(UsernameForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username'].lower()

        if not username:
            raise forms.ValidationError('Неверное имя пользователя.')

        already_user = User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists()

        if already_user:
            raise forms.ValidationError(
                'Данное имя пользователя уже используется другим участником.'
                ' Пожалуйста, используйте что-то более оригинальное.'
            )

        return username


def get_wave_tariff_choices():
    tariffs = Tariff.objects.filter(
        slug__in=settings.NEWBIE_SELECTION_WAVE_TARIFFS
    ).select_related(
        'tariff_group'
    ).order_by('fee_rub').all()

    tariffs_choices = [
        (t.id, {
            'title': t.title,
            'price': t.fee_rub,
            'price_eur': t.fee_eur,
            'duration': t.duration,
            'duration_unit': t.duration_unit_to_str,
            'is_wave': t.tariff_group.is_wave,
        })
        for t in tariffs
    ]

    return tariffs_choices


class TariffCampaignForm(forms.Form):
    campaign = forms.ModelChoiceField(
        queryset=Campaign.objects.none(), label='Желаемая дата старта',
        empty_label="Пока не знаю", required=False
    )

    wave_tariff = forms.ChoiceField(
        choices=get_wave_tariff_choices,
        label='Тариф',
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

        super(TariffCampaignForm, self).__init__(*args, **kwargs)

        min_start_date = datetime.date.today() - datetime.timedelta(days=8)
        self.fields['campaign'].queryset = Campaign.objects.filter(
            Q(start_date__gte=min_start_date, is_active=True) | Q(pk=self.user.application.campaign_id))


class DiaryDataForm(forms.Form):
    steps = forms.IntegerField(min_value=0, max_value=50000, required=False, label="Шаги")
    sleep_hours = forms.IntegerField(min_value=0, max_value=23, required=False, label="Сон (часы)")
    sleep_minutes = forms.IntegerField(min_value=0, max_value=60, required=False, label="Сон (минуты)")
    weight = forms.DecimalField(min_value=10, max_value=400, required=False, label="Вес", decimal_places=3)
    meals_score = forms.IntegerField(min_value=1, max_value=10, required=False, label="Полноценность")
    meals_faults = forms.IntegerField(min_value=0, max_value=5, required=False, label="Жиронакопление")
    meals_overcalory = forms.BooleanField(required=False, label="Дополнительные продукты")


class AnalysisAdminForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea)

    adjust_calories = forms.IntegerField(label='Калорийность рациона', min_value=-100, max_value=100, required=False)
    adjust_protein = forms.IntegerField(label='Белковость рациона', min_value=-100, max_value=100, required=False)
    add_fat = forms.BooleanField(label='Добавить жиров', required=False)
    adjust_fruits = forms.ChoiceField(label='Ограничение фруктов', initial='NO', required=False, choices=(
        ('NO', 'без дополнительных ограничений'),
        ('RESTRICT', 'ограничение фруктов'),
        ('EXCLUDE', 'замена фруктов'),
    ))
    adjust_carb_mix_vegs = forms.BooleanField(label='Смешивать овощи', required=False)
    adjust_carb_bread_min = forms.BooleanField(label='Минимизировать хлеб', required=False)
    adjust_carb_bread_late = forms.BooleanField(label='Убрать хлеб из ужина', required=False)
    adjust_carb_carb_vegs = forms.BooleanField(label='Исключить запасающие овощи после обеда', required=False)
    adjust_carb_sub_breakfast = forms.BooleanField(label='Замена длинных углеводов на овощи (завтрак по схеме обеда)',
                                                   required=False)
    exclude_lactose = forms.BooleanField(label='Исключить молочные сахара', required=False)
    restrict_lactose_casein = forms.BooleanField(
        label='Ограничить молочные сахара и казеин вторым завтраком', required=False
    )

    alarm = forms.ChoiceField(label='Аларм', required=False,
                              choices=(('TEST', _("Необходимо специализированное обследование")),
                                       ('OBSERVATION', _("Имеются особенности обмена, требуется наблюдение")),
                                       ('TREATMENT', _("Под наблюдением врачей")),
                                       ('DANGER', _("Необходимо лечение, требуется посещение врача")),
                                       ('PR', _("Необходимо постоянное следование персональным рекомендациям")),
                                       ('OOC', _("Питание не соответствует методичке и общим рекомендациям проекта")),
                                       ('OK', _("Всё ок")))
                              )


class ProductModerationForm(forms.ModelForm):
    alias_of = forms.ModelChoiceField(
        queryset=MealProduct.objects.filter(is_verified=True).all(),
        to_field_name='id',
        label='Основной продукт', required=False,
        widget=autocomplete.ModelSelect2(
            url='srbc:staff-meal-product-moderation-search',
            attrs={
                # Set some placeholder
                'data-placeholder': 'Поиск ...',
                # Only trigger autocomplete after 3 characters have been typed
                'data-minimum-input-length': 3,
            },
        )
    )

    protein_percent = forms.FloatField(label='Белки', min_value=0, max_value=100, required=False)
    fat_percent = forms.FloatField(label='Жиры', min_value=0, max_value=100, required=False)
    carb_percent = forms.FloatField(label='Углеводы', min_value=0, max_value=100, required=False)
    is_fast_carbs = forms.BooleanField(label='Содержит простые углеводы', required=False)
    is_alco = forms.BooleanField(label='Содержит алкоголь', required=False)

    class Meta:
        model = MealProductModeration
        fields = [
            'title',
            'status',
            'component_type',
            'rejection_reason',
            'alias_of',
        ]

    def clean_title(self):
        title = self.cleaned_data.get('title')
        status = self.data.get('status')

        if not status:
            self.add_error('status', 'Необходимо указать статус')

        if status in ('APPROVED_NEW', 'REJECTED_REMOVE', 'REJECTED_IGNORE', 'REJECTED_REPLACE'):
            if MealProduct.objects.filter(title=title).exists():
                self.add_error('title', 'Продукт с таким названием уже существует')

        return title

    def clean_component_type(self):
        component_type = self.cleaned_data.get('component_type')
        status = self.cleaned_data.get('status')

        if component_type and status != 'APPROVED_NEW':
            self.add_error('component_type', 'Выбор продукта доступен при создании нового продукта.')

        if not component_type and status == 'APPROVED_NEW':
            self.add_error('component_type', 'Нужно выбрать продукт.')

        return component_type

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if status == 'PENDING':
            self.add_error('status', 'Необходимо провести модерацию продукта.')
        return status

    def clean_alias_of(self):
        alias_of = self.cleaned_data.get('alias_of')
        status = self.cleaned_data.get('status')

        if status in ('APPROVED_ALIAS', 'REJECTED_REPLACE'):
            if not alias_of:
                self.add_error('alias_of', 'Необходимо указать продукт.')
        else:
            if alias_of:
                self.add_error('alias_of', 'Может быть указано для синонимов или при замене продукта в рационе.')

        return alias_of

    def is_valid_bzu(self, value):
        component_type = self.cleaned_data.get('component_type')
        if (component_type in ('unknown', 'mix')) and (value is None):
            return False

        return True

    def clean_protein_percent(self):
        value = self.cleaned_data.get('protein_percent')
        if not self.is_valid_bzu(value):
            self.add_error(
                'protein_percent',
                'Если выбран "Продукт с неопределенным составом" или "Сложная смесь", то БЖУ должны быть указаны.'
            )
        return value

    def clean_fat_percent(self):
        value = self.cleaned_data.get('fat_percent')
        if not self.is_valid_bzu(value):
            self.add_error(
                'fat_percent',
                'Если выбран "Продукт с неопределенным составом" или "Сложная смесь", то БЖУ должны быть указаны.'
            )
        return value

    def clean_carb_percent(self):
        value = self.cleaned_data.get('carb_percent')
        if not self.is_valid_bzu(value):
            self.add_error(
                'carb_percent',
                'Если выбран "Продукт с неопределенным составом" или "Сложная смесь", то БЖУ должны быть указаны.'
            )

        protein_percent = self.cleaned_data.get('protein_percent') or 0
        fat_percent = self.cleaned_data.get('fat_percent') or 0
        carb_percent = value or 0

        if protein_percent + fat_percent + carb_percent > 100:
            self.add_error(
                'protein_percent',
                'БЖУ должны быть указаны на 100г'
            )
            self.add_error(
                'fat_percent',
                'БЖУ должны быть указаны на 100г'
            )
            self.add_error(
                'carb_percent',
                'БЖУ должны быть указаны на 100г'
            )

        return value


class DateInput(forms.DateInput):
    input_type = 'date'

class ProdamusPaymentForm(forms.Form):
    user = forms.ModelChoiceField(label="Пользователь", queryset=User.objects.all())
    tariff = forms.ModelChoiceField(label="Тариф", queryset=Tariff.objects.filter(is_archived=False))
    wave = forms.ModelChoiceField(label="Поток", queryset=Wave.objects.filter(is_archived=False), required=False)
    date_start = forms.DateField(label="Дата начала", widget=DateInput)
    date_end = forms.DateField(label="Дата конца", widget=DateInput)
    price_rub = forms.DecimalField(label="Цена в рублях" ,decimal_places=2)