from datetime import date, timedelta

from django.conf import settings
from srbc.models import Tariff, TariffGroup
from srbc.utils.helpers import pluralize


def get_active_subscriptions():
    # TODO пока список в сеттингах задается
    # subscription_tariffs = Tariff.objects.filter(
    #     tariff_group__is_wave=False
    # ).select_related(
    #     'tariff_group'
    # ).all()

    subscription_tariffs = Tariff.objects.filter(
        slug__in=settings.ACTIVE_SUBSCRIPTION_TARIFFS
    ).select_related(
        'tariff_group'
    ).all()

    return subscription_tariffs


# является ли переход с тарифа tariff_from на tariff_to апгрейдом
def is_upgrade(tariff_from, tariff_to):
    slugs = settings.SUBSCRIPTION_UPGRADE_ABILITY.get(tariff_from.slug, [])
    return tariff_to.slug in slugs


# является ли переход с тарифа tariff_from на tariff_to апгрейдом
def is_sidegrade(tariff_from, tariff_to):
    for item in settings.SUBSCRIPTION_SIDEGRADE_ABILITY:
        tariffs = item.get('tariffs', [])
        if tariff_from.slug in tariffs and tariff_to.slug in tariffs:
            return True, item.get('transition_tariff')

    return False, None


def is_downgrade(tariff_from, tariff_to):
    sidigrade, _ = is_sidegrade(tariff_from, tariff_to)
    return not sidigrade and not is_upgrade(tariff_from, tariff_to)


def get_subscription_tariffS_data():
    subscription_tariffs = get_active_subscriptions()

    subscription_tariffs_data = [
        {
            "slug": t.slug,
            "title": t.title,
            "price_eur": t.fee_eur,
            "price_rub": t.fee_rub,
            "duration": t.duration,
            "duration_unit": t.duration_unit_to_str(),
            "meeting_access": t.tariff_group.meetings_access,
            "diary_access": t.tariff_group.diary_access,
            "is_wave": t.tariff_group.is_wave,
        }
        for t in subscription_tariffs
    ]

    return subscription_tariffs_data


# рассчитвает необходию доплату при переходе с одного тарифа на другой
# from_date - дата, от которой вычисляем
def get_changing_surcharge(old_tariff, new_tariff, end_date, from_date=None):
    from_date = from_date or date.today()

    # вычисляем разницу в днях
    days_diff = (end_date - from_date).days

    # вычисляем стоимость одного дня для каждого тарифа
    old_tariff_day_price = old_tariff.fee_eur / old_tariff.duration_in_days
    new_tariff_day_price = new_tariff.fee_eur / new_tariff.duration_in_days

    price_diff = (new_tariff_day_price - old_tariff_day_price) * days_diff

    return price_diff


# возвращает данные о смене текущей подписки
# полный набор для каждого потенциального перехода
def get_subscription_changing_data(tariff, end_date):
    result = []

    subscription_tariffs = get_active_subscriptions()
    for new_tariff in subscription_tariffs:
        # базовая инфа для любого тарифа
        info = {
            "slug": new_tariff.slug,
            "title": new_tariff.title,
            "price": new_tariff.fee_eur,
            "duration": new_tariff.duration,
            "duration_unit": new_tariff.duration_unit_to_str(),
            "meeting_access": new_tariff.tariff_group.meetings_access,
            "diary_access": new_tariff.tariff_group.diary_access,
        }

        changing_data = {}
        if new_tariff != tariff:
            # общее для всех текстов
            # end_date = subscription.user.profile.active_tariff_history.valid_until
            changing_data['renewal_data'] = end_date + timedelta(days=1)

            today = date.today()
            # проверяем является ли данный переход апгрейдом
            if is_upgrade(tariff, new_tariff):
                changing_data['mode'] = 'upgrade'
                changing_data['price_delta'] = round(get_changing_surcharge(
                    tariff, new_tariff, end_date, today), 2)
                days_diff = (end_date - today).days
                changing_data['renewal_period'] = '%s %s' % (days_diff, pluralize(days_diff, ['день', 'дня', 'дней']))
                #  RENEWAL_PERIOD и AMOUNT период в тексте пояснения кажется, что одно и тоже

            # проверяем является ли данный переход сайдгрейдом
            else:
                sidegrade, transition = is_sidegrade(tariff, new_tariff)
                if sidegrade:
                    transition_tariff = Tariff.objects.get(slug=transition)

                    changing_data['mode'] = 'sidegrade'
                    changing_data['transition_tariff'] = transition_tariff.title
                    changing_data['transition_price'] = transition_tariff.fee_eur
                    changing_data['amount'] = round(get_changing_surcharge(
                        tariff, transition_tariff, end_date, today), 2)

                else:
                    changing_data['mode'] = 'downgrade'

        info['changing_data'] = changing_data
        result.append(info)

    return result


def get_subscription(diary_access, meeting_access):
    tariff = Tariff.objects
    if meeting_access:
        tariff = tariff.exclude(tariff_group__meetings_access=TariffGroup.MEETINGS_NO_ACCESS)
    else:
        tariff = tariff.filter(tariff_group__meetings_access=TariffGroup.MEETINGS_NO_ACCESS)

    tariff = tariff.filter(
        tariff_group__diary_access=diary_access,
        slug__in=settings.ACTIVE_SUBSCRIPTION_TARIFFS
    )

    return tariff.first()
