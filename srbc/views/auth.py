# -*- coding: utf-8 -*-
import hmac
import logging

from datetime import datetime, date
from hashlib import sha256
from time import time

from django.conf import settings
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from markdownx.utils import markdownify

from crm.forms import AdmissionTestAskQuestionForm, AdmissionTestQuestionForm
from crm.models import AdmissionTestQuestion, UserAdmissionTest, UserAdmissionTestQuestion
from crm.models import DiscountCode
from crm.utils.payments import get_payment_amount, build_order, \
    make_ya_payment, make_pp_payment, make_stripe_payment, \
    get_payment_wave, get_payment_dates
from crm.utils.subscription import get_subscription_tariffS_data
from srbc.decorators import validate_user, has_desktop_access
from srbc.forms import (
    InviteForm, ApplicationForm,
    RealNameForm, TariffCampaignForm,
    DiscountForm,
    UsernameForm,
    PhoneForm,
)
from srbc.models import Profile, UserNote
from srbc.utils.auth import ProgressBar, get_short_time_jwt

logger = logging.getLogger(__name__)


@login_required
@has_desktop_access
def blocked_user(request):
    if request.user.profile.is_active:
        return redirect('/')

    if not request.user.profile.last_active_tariff_history_record:
        return redirect('/')

    info = {}

    subscription_tariffs_data = get_subscription_tariffS_data()
    info['subscription_tariffs'] = subscription_tariffs_data

    if request.user.profile.tariff_next:
        next_payment_from, next_payment_until = get_payment_dates(request.user, request.user.profile.tariff_next)
        info['next_payment_from'] = next_payment_from
        info['next_payment_until'] = next_payment_until
    else:

        info['stripe_pk'] = settings.STRIPE_PUBLIC_KEY

    return render(
        request,
        'registration/blocked.html',
        info
    )


@login_required
@has_desktop_access
def mobile_tariff(request):
    return render(
        request,
        'registration/blocked_mobile.html',
        {
        }
    )


@login_required
def desktop_no_access(request):
    return render(
        request,
        'registration/blocked_desktop_access.html',
        {
        }
    )


@login_required
@has_desktop_access
def social_acc_rejected(request):
    if request.user.application.social_acc_status != 'REJECTED':
        return redirect('/')

    return render(
        request,
        'registration/social_blocked.html',
        {
        }
    )


@login_required
@has_desktop_access
def payment(request):
    bar = ProgressBar(request.user, "payment")
    # FIXME вот тут вторая часть проверки будет проходить всегда получается, поля wave_id нету.
    # if not bar.can_be_here() and not request.user.profile.last_active_tariff_history_record:
    if not bar.can_be_here() and not request.user.profile.tariff_next_id:
        return redirect('/')

    if request.user.profile.is_blocked:
        return redirect('/blocked/')

    with transaction.atomic():
        # Locking
        Profile.objects.select_for_update().get(user=request.user)

        # last_user_bill = Order.objects.filter(user=request.user).order_by('-date_added').first()
        # has_unpaid_bills = last_user_bill is not None and last_user_bill.status == 'PENDING'

        invite_form = None
        discount_form = None
        pp_form = None
        stripe_session_id = None

        existing_order = request.user.application.active_payment_order

        if existing_order:
            if existing_order.status in ['PENDING', 'PROCESSING', ]:
                if existing_order.payment_provider == 'PP' and existing_order.payment_id:
                    existing_order, pp_form = make_pp_payment(existing_order, request)
                elif existing_order.payment_provider == 'STRIPE' and existing_order.payment_id:
                    existing_order, stripe_session_id = make_stripe_payment(existing_order, request)

        elif request.user.application.is_payment_allowed:
            existing_order = build_order(request.user)
            request.user.application.active_payment_order = existing_order
            request.user.application.save(update_fields=['active_payment_order'])

        allowed_payment_methods = settings.ALLOWED_PAYMENT_METHODS
        # if request.user.profile.communication_mode == 'CHAT':
        #     allowed_payment_methods = ['PP']

    if request.method == 'POST':
        # if request.POST.get('action') == 'invite':
        #     if existing_order and existing_order.payment_id:
        #         return redirect('/payment/')

        #     invite_form = InviteForm(request.POST, user=request.user)
        #     if invite_form.is_valid():
        #         invite = Invitation.objects.get(code=invite_form.cleaned_data.get('code'))
        #         invite.applied_by = request.user
        #         invite.applied_at = datetime.now()
        #         invite.is_applied = True
        #         invite.save()

        #         if invite.wave:
        #             request.user.profile.wave = invite.wave

        #         if invite.communication_mode:
        #             request.user.profile.communication_mode = invite.communication_mode

        #         _wave, request.user.profile.valid_until = get_valid_until_date(request.user, days=invite.days_paid)

        #         request.user.profile.is_active = True
        #         request.user.profile.save(update_fields=['is_active', 'wave', 'valid_until', 'communication_mode'])

        #         request.user.application.active_payment_order = None
        #         request.user.application.save(update_fields=['active_payment_order'])

        #         return redirect('/dashboard/')

        if request.POST.get('action') == 'set_payment':
            payment_method = request.POST.get('provider')
            if existing_order and existing_order.payment_id:
                return redirect('/payment/')

            if payment_method in allowed_payment_methods:
                existing_order.payment_provider = payment_method
                existing_order.amount, existing_order.currency = get_payment_amount(existing_order)
                existing_order.wave = get_payment_wave(user=request.user, tariff=existing_order.tariff)
                existing_order.save(update_fields=['payment_provider', 'amount', 'currency', 'wave'])

        if request.POST.get('action') == 'set_discount':
            discount_form = DiscountForm(request.POST, user=request.user)
            if discount_form.is_valid():
                discount_code = discount_form.cleaned_data.get('code')
                # print discount_code
                if discount_code:
                    discount = DiscountCode.objects.get(code=discount_code)
                    discount.applied_by = request.user
                    discount.applied_at = datetime.now()
                    discount.is_applied = True
                    discount.save()
                    existing_order.discount_code = discount
                    existing_order.amount, existing_order.currency = get_payment_amount(existing_order)
                    existing_order.wave = get_payment_wave(user=request.user, tariff=existing_order.tariff)
                    existing_order.save(update_fields=['discount_code', 'amount', 'currency', 'wave'])

        if request.POST.get('action') == 'make_payment':
            if existing_order.payment_id:
                return redirect('/payment/')

            if not request.user.application.tos_signed_date and request.POST.get('tos_signed'):
                request.user.application.tos_signed_date = timezone.now()
                request.user.application.save(update_fields=['tos_signed_date'])

            if request.user.application.tos_signed_date:
                if existing_order.payment_provider == 'YA':
                    existing_order = make_ya_payment(existing_order, request,
                                                     settings.RUSSIAN_PAYMENT_ALLOWED_METHODS['BANK_CARD'])
                    if existing_order.payment_url:
                        return redirect(existing_order.payment_url)
                if existing_order.payment_provider == 'YM':
                    existing_order = make_ya_payment(existing_order, request,
                                                     settings.RUSSIAN_PAYMENT_ALLOWED_METHODS['YOO_MONEY'])
                    if existing_order.payment_url:
                        return redirect(existing_order.payment_url)
                if existing_order.payment_provider == 'PP':
                    existing_order, pp_form = make_pp_payment(existing_order, request)
                if existing_order.payment_provider == 'STRIPE':
                    existing_order, stripe_session_id = make_stripe_payment(existing_order, request)

    if invite_form is None:
        invite_form = InviteForm()

    if discount_form is None:
        initial_discount = {}
        if existing_order is not None and existing_order.discount_code:
            initial_discount.update({"code": existing_order.discount_code.code})
        discount_form = DiscountForm(initial=initial_discount)

    return render(
        request,
        'registration/payment.html',
        {
            'stripe_pk': settings.STRIPE_PUBLIC_KEY,
            'form_invite': invite_form,
            'discount_form': discount_form,
            'pp_form': pp_form,
            'stripe_session_id': stripe_session_id,
            'order': existing_order,
            "progress_bar": bar.route(),
        }
    )


def logout_view(request):
    logout(request)
    return redirect('/')


@login_required
@has_desktop_access
def user_names(request):
    bar = ProgressBar(request.user, "names")
    if not bar.can_be_here():
        return redirect('/')

    if request.user.profile.is_active \
            and request.user.profile.has_wave_tariff_history \
            and request.user.application.first_name \
            and request.user.application.last_name:
        return redirect('/')

    if request.method == 'POST':
        form = RealNameForm(request.POST)
        if form.is_valid():
            request.user.application.first_name = form.cleaned_data.get('first_name')
            request.user.application.last_name = form.cleaned_data.get('last_name')

            request.user.first_name = form.cleaned_data.get('first_name')
            request.user.last_name = form.cleaned_data.get('last_name')

            request.user.application.save(update_fields=['first_name', 'last_name'])
            request.user.save(update_fields=['first_name', 'last_name'])

            return redirect('/')
    else:
        form = RealNameForm(initial={
            "first_name": request.user.application.first_name or request.user.first_name,
            "last_name": request.user.application.last_name or request.user.last_name,
        })

    return render(
        request,
        'registration/nomail.html',
        {
            'form': form,
            'application': request.user.application,
            'progress_bar': bar.route(),

        }
    )


@login_required
@has_desktop_access
def user_username(request):
    bar = ProgressBar(request.user, "username")
    if not bar.can_be_here():
        return redirect('/')

    if request.user.profile.is_active and not request.user.profile.username_is_editable and request.user.profile.has_wave_tariff_history:
        return redirect('/')

    if request.method == 'POST':
        form = UsernameForm(request.POST, user=request.user)
        if form.is_valid():
            old_username = request.user.username
            request.user.username = form.cleaned_data.get('username')
            request.user.profile.username_is_editable = False
            request.user.save(update_fields=['username'])
            request.user.profile.save(update_fields=['username_is_editable'])

            if request.user.username != old_username:
                note = UserNote(
                    user=request.user,
                    date_added=date.today(),
                    label='NB',
                    is_published=False,
                    content="Имя пользователя изменено с **%s** на **%s**" % (
                        old_username,
                        request.user.username,
                    ),
                    author_id=settings.SYSTEM_USER_ID
                )
                note.save()
            return redirect('/')
    else:
        username = request.user.username
        form = UsernameForm(initial={'username': username})

    return render(
        request,
        'registration/username.html',
        {
            'form': form,
            'progress_bar': bar.route(),
        }
    )


# @login_required
# def user_campaign_selection(request):
#     if request.user.profile.wave:
#         return redirect('/')
#
#     if request.method == 'POST':
#         form = UserCampaignForm(request.POST)
#         if form.is_valid():
#             request.user.application.campaign_id = form.cleaned_data.get('campaign_id')
#             request.user.application.save(update_fields=['campaign'])
#             # TODO: add email to Mailchimp group
#             return redirect('/')
#     else:
#         form = UserCampaignForm()
#
#     return render(
#         request,
#         'registration/campaign.html',
#         {
#             'form': form,
#             'application': request.user.application,
#         }
#     )


def welcome(request):
    if request.user.pk:
        return redirect('/')

    templates = {
        0: '0_not_started',
        1: '1_signup',
        9: '9_countdown_start',
        99: '99_not_active',
    }

    registration_open_time = datetime(year=2017, month=6, day=21, hour=18, minute=30, second=0)

    # step = 1 if datetime.now() > registration_open_time else 0
    step = 1

    if request.GET.get('patience') == '0':
        step = 1

    bar = ProgressBar(request.user, "login")
    if not bar.can_be_here():
        return redirect('/')

    return render(
        request,
        'registration/welcome_%s.html' % templates.get(step),
        {
            "progress_bar": bar.route(),
            "reg_date": [
                registration_open_time.year,
                registration_open_time.month,
                registration_open_time.day,
                registration_open_time.hour,
                registration_open_time.minute,
                registration_open_time.second,
            ]
        }
    )


def tg_login_view(request):
    request_data = request.GET.copy()

    token_time = int(request_data.get('auth_date', 0))
    current_time = int(time())

    bot_token = settings.DJANGO_TELEGRAMBOT['BOTS'][0]['TOKEN']
    login_key = sha256(bot_token.encode()).digest()
    login_hash = request_data.get('hash')
    request_data.pop('hash', None)

    request_data_sorted = sorted(request_data.items(), key=lambda x: x[0])

    data_check_string = []

    for data_pair in request_data_sorted:
        key, value = data_pair[0], data_pair[1]
        data_check_string.append('%s=%s' % (key, value,))

    login_string = '\n'.join(data_check_string)

    login_data_hash = hmac.new(login_key, msg=login_string.encode(), digestmod=sha256).hexdigest()

    if login_data_hash != login_hash:
        return render(
            request,
            'registration/tg_login_error.html',
            {
                'reason': 'incorrect_link'
            }
        )

    if token_time + 600 < current_time:
        return render(
            request,
            'registration/tg_login_error.html',
            {
                'reason': 'expired_link'
            }
        )

    try:
        profile = Profile.objects.get(telegram_id=request_data.get('id'))
    except Profile.DoesNotExist:
        return render(
            request,
            'registration/tg_login_error.html',
            {
                'reason': 'unknown_user'
            }
        )

    user = profile.user

    if not user:
        return render(
            request,
            'registration/tg_login_error.html',
            {
                'reason': 'profile_error'
            }
        )

    login(request=request, user=user, backend='django.contrib.auth.backends.ModelBackend')

    return redirect('/')


def login_form(request):
    if request.user.is_authenticated:
        next_location = request.GET.get('next', '/')
        return redirect(next_location)
    else:
        from django.contrib.auth.views import LoginView, AuthenticationForm  # TODO: move in import section

        return LoginView.as_view(
            template_name='registration/login.html',
            redirect_field_name='next',
            form_class=AuthenticationForm,
            extra_context={
                'bot_name': settings.DJANGO_TELEGRAMBOT['BOTS'][0]['NAME'],
                'base_url': 'https://' + request.get_host(),
            },
            redirect_authenticated_user=False,
        )(request)


def registration(request):
    if request.user.is_authenticated:
        next_location = request.GET.get('next', '/')
        return redirect(next_location)
    else:
        return render(
            request,
            'registration/registration.html',
            {
            }
        )


@login_required
def auth_mobile(request):
    token = get_short_time_jwt(request.user)

    return render(
        request,
        'registration/mobile_auth.html',
        {
            'token': token
        }
    )


@login_required
@has_desktop_access
def application_form(request):
    bar = ProgressBar(request.user, "application")
    if not bar.can_be_here():
        return redirect('/')

    my_application = request.user.application

    if not my_application.is_approved and request.method == 'POST':
        form = ApplicationForm(request.POST, instance=my_application, user=request.user)
        if form.is_valid():
            my_application = form.save(commit=False)
            my_application.email = request.user.email
            my_application.is_approved = False
            my_application.save(update_fields=['email', 'is_approved'])

            request.user.first_name = my_application.first_name
            request.user.last_name = my_application.last_name

            request.user.save()

            request.user.profile.gender = my_application.gender
            request.user.profile.height = my_application.height
            request.user.profile.birth_year = my_application.birth_year
            request.user.profile.goal_weight = my_application.goal_weight
            request.user.profile.baby_case = my_application.baby_case
            request.user.profile.baby_birthdate = my_application.baby_birthdate

            request.user.profile.save(update_fields=[
                'gender', 'height', 'birth_year',
                'baby_case', 'baby_birthdate',
            ])

            return redirect('/')
    else:
        form = ApplicationForm(
            instance=my_application, user=request.user
        )

    return render(
        request,
        'registration/application.html',
        {
            'form': form,
            'application': request.user.application if hasattr(request.user, 'application') else None,
            'progress_bar': bar.route(),
        }
    )


def social_register(request, backend):
    request.session['social_registration_allowed_%s' % backend] = True
    redirect_url = '/login/%s/?%s' % (backend, request.GET.urlencode())

    return redirect(redirect_url)


def link_social_anonimously(request, link_key=None):
    pass


def get_link_social_anonimously(request):
    pass


def link_instagram_secure(request, userkey):
    if not userkey:
        return redirect('/')

    key_user = Profile.objects.filter(instagram_link_code=userkey).first()

    if not key_user:
        return redirect('/')

    if not key_user.is_active:
        return redirect('/')

    if request.user.is_authenticated and request.user.pk != key_user.user_id:
        return redirect('/instagram/')

    request.session['instagram_secure_linking'] = userkey
    return redirect('/instagram/')


@login_required
@has_desktop_access
def link_telegram(request):
    bar = ProgressBar(request.user, 'telegram')
    if not bar.can_be_here():
        return redirect('/')

    is_check = request.GET.get('check', None)

    if request.method == 'POST':
        form = PhoneForm(request.POST, user=request.user)
        if form.is_valid():
            request.user.profile.mobile_number = form.cleaned_data.get('phone')
            request.user.profile.save(update_fields=['mobile_number'])

    else:
        form = PhoneForm(initial={
            "phone": request.user.profile.mobile_number
        })

    return render(
        request,
        'registration/telegram.html',
        {
            "progress_bar": bar.route(),
            "form": form,
            "is_check": is_check,
        }
    )


@login_required
@has_desktop_access
def admission_required(request):
    bar = ProgressBar(request.user, 'admission')
    if not bar.can_be_here():
        return redirect('/')

    if request.user.profile.wave:
        return redirect('/')

    if request.user.profile.communication_mode == 'CHAT':
        return redirect('/')

    if not request.user.application.campaign:
        return redirect('/')

    if request.user.application.campaign.is_admission_open:
        try:
            admission_test = request.user.admission_test
        except User.admission_test.RelatedObjectDoesNotExist:
            admission_test = UserAdmissionTest()
            admission_test.user = request.user
            admission_test.status = 'IN_PROGRESS'
            admission_test.save()

            test_questions_count = 4
            questions_for_user = AdmissionTestQuestion.objects.filter(
                is_active=True
            ).order_by('?')[:test_questions_count]

            for i, question in enumerate(questions_for_user):
                test_question = UserAdmissionTestQuestion()
                test_question.admission_test = admission_test
                test_question.question_num = i + 1
                test_question.text = question.text
                test_question.is_answered = False
                test_question.source_question = question
                test_question.save()

        explicit_part = request.GET.get('part')
        # print request.GET
        explicit_question = request.GET.get('q')
        current_question = None
        questions_count = UserAdmissionTestQuestion.objects.filter(admission_test=admission_test).count()

        if explicit_part == 'T' and explicit_question:
            current_question = UserAdmissionTestQuestion.objects.filter(
                admission_test=admission_test, question_num=explicit_question).first()

        if not current_question and explicit_part != 'Q':
            current_question = UserAdmissionTestQuestion.objects.filter(
                admission_test=admission_test, is_answered=False).order_by('question_num').first()

        has_unanswered_questions = UserAdmissionTestQuestion.objects.filter(
            admission_test=admission_test, is_answered=False).count()

        exam_part = None
        form = None

        if admission_test.status == 'IN_PROGRESS':
            if not request.user.application.campaign.is_admission_open:
                exam_part = 'B'
                form = None
            elif current_question or explicit_part == 'T':
                exam_part = 'T'
                if request.method == 'POST':
                    form = AdmissionTestQuestionForm(request.POST, instance=current_question)
                    if form.is_valid():
                        form.save()
                        current_question.is_answered = True
                        current_question.save(update_fields=['is_answered'])

                        return redirect('/admission/')
                else:
                    current_question.text = markdownify(current_question.text)
                    form = AdmissionTestQuestionForm(instance=current_question)

            # elif not admission_test.question_asked or explicit_part == 'Q':
            else:
                exam_part = 'Q'
                if request.method == 'POST':
                    form = AdmissionTestAskQuestionForm(request.POST, instance=admission_test)
                    if form.is_valid():
                        form.save()
                        admission_test.status = 'DONE'
                        admission_test.save(update_fields=['status', 'completed_date'])
                        return redirect('/')
                else:
                    form = AdmissionTestAskQuestionForm(instance=admission_test)
            # else:
            #     exam_part = 'R'
            #     if request.method == 'POST':
            #         form = AdmissionTestRecommendationForm(request.POST, instance=admission_test)
            #         if form.is_valid():
            #             form.save()
            #             admission_test.status = 'DONE'
            #             admission_test.save(update_fields=['status', 'completed_date'])
            #             return redirect('/')
            #     else:
            #         form = AdmissionTestRecommendationForm(instance=admission_test)
    else:
        try:
            admission_test = request.user.admission_test
        except User.admission_test.RelatedObjectDoesNotExist:
            admission_test = UserAdmissionTest()
            admission_test.user = request.user
            admission_test.status = 'IN_PROGRESS'

        questions_count = None
        current_question = None
        has_unanswered_questions = None
        form = None
        exam_part = None

    return render(
        request,
        'registration/admission.html',
        {
            "progress_bar": bar.route(),
            "admission_test": admission_test,
            "questions_count": questions_count,
            "current_question": current_question,
            "unanswered_questions": has_unanswered_questions,
            "form": form,
            "part": exam_part,

            "test_statuses_pending": ['DONE', 'FAILED', 'PASSED'],
        }
    )


@login_required
@has_desktop_access
@validate_user
def agreement_sign(request):
    if request.method == 'POST':
        signature = request.POST.get('signature', '')
        signature = signature.lower().strip()
        if signature == request.user.username.lower():
            request.user.profile.agreement_signed_date = timezone.localtime()
            request.user.profile.save(update_fields=['agreement_signed_date'])
        next_action = request.POST.get('next')
    else:
        next_action = request.GET.get('next', '/')

    if request.user.profile.agreement_signed_date:
        return redirect(next_action)

    return render(
        request,
        'registration/agreement_sign.html',
        {
            "next": next_action,
        }
    )


@login_required
@has_desktop_access
def tariff_selection(request):
    # if request.user.profile.is_active and request.user.profile.has_wave_tariff_history:
    #     return redirect('/')

    bar = ProgressBar(request.user, 'tariff')
    if not bar.can_be_here():
        return redirect('/')

    subscription_tariffs_data = get_subscription_tariffS_data()

    if request.method == 'POST' and request.POST.get('action') == 'save':
        form = TariffCampaignForm(request.POST, user=request.user)
        if form.is_valid():
            print(form.cleaned_data)
            request.user.application.campaign = form.cleaned_data.get('campaign')
            request.user.application.tariff_id = form.cleaned_data.get('wave_tariff') or None
            request.user.application.save(update_fields=['campaign', 'tariff_id'])

            if request.user.application.campaign:
                return redirect('/')
            else:
                bar = ProgressBar(request.user, 'tariff')
        else:
            print(form.errors)

    else:
        form = TariffCampaignForm(initial={
            "campaign": request.user.application.campaign,
            "tariff": request.user.application.tariff,
        }, user=request.user)

    return render(
        request,
        'registration/tariff_selection.html',
        {
            "current_campaign": request.user.application.campaign,
            "current_tariff": request.user.application.tariff,
            "form": form,
            "progress_bar": bar.route(),
            "subscription_tariffs": subscription_tariffs_data,
            'stripe_pk': settings.STRIPE_PUBLIC_KEY
        }
    )
