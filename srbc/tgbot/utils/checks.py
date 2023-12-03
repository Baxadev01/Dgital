import logging
import typing as ty

from django.db import connection, OperationalError, InterfaceError
from django.utils import timezone

from crm.models import Campaign
from srbc.models import User
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.utils import translate

__all__ = ('check_user', )

logger = logging.getLogger(__name__)


def check_user(tg_user_id: int) -> ty.Tuple[ty.Optional[User], ty.Optional[ty.Text]]:
    """ Checks user settings to pass this user to work with nodes. """
    try:
        user = User.objects.filter(profile__telegram_id=tg_user_id).select_related('profile').first()
    except (OperationalError, InterfaceError):
        connection.close()
        user = User.objects.filter(profile__telegram_id=tg_user_id).select_related('profile').first()

    today_date = timezone.now().date()

    # проверим, что бот не знаком с участником
    if not user:
        return user, translate(NodeTranslations.GO_TO__CMD__START)

    if user.profile.is_active and not user.profile.wave:
        return user, translate(NodeTranslations.CLIENT__NO_WAVE)
    else:
        # получается у нас есть юзер, который участвовал /участвует в какой-то волне.
        if user.profile.is_active and user.profile.valid_until >= today_date:
            # активный участник или будущий участник
            if user.profile.wave.start_date <= today_date:
                # активный участник
                return user, None
            else:
                # будущий участник
                if user.application and user.application.campaign:
                    campaign = user.application.campaign
                else:
                    # campaign отсутствует
                    return user, translate(NodeTranslations.FUTURE_CLIENT__NO_CAMPAIGN)

                # находим ближайшую дату компании
                try:
                    nearest_campaign = Campaign.objects.filter(start_date__gt=today_date).earliest('start_date')
                except Campaign.DoesNotExist:
                    return user, translate(NodeTranslations.CAMPAIGN__NEAREST__UNDEFINED)

                # campaign привязан к ближайшей дате
                if campaign == nearest_campaign:
                    # формат участия = 'канал'
                    if user.profile.communication_mode == 'CHANNEL':
                        # admission test: [отсутствует | "не дошел" | "в процессе"]
                        if not user.admission_test or user.admission_test.status in ('NOT_STARTED', 'IN_PROGRESS'):
                            text = translate(NodeTranslations.FUTURE_CLIENT__CAMPAIGN__CHANNEL__NOT_FINISHED_TEST)
                            text = text.format(START_DATE=campaign.start_date)
                            return user, text
                        # admission test: ["завершил" | "проверено, все ок" | "проверено, завалил"]
                        elif user.admission_test.status in ('DONE', 'PASSED', 'FAILED'):
                            text = translate(NodeTranslations.FUTURE_CLIENT__CAMPAIGN__CHANNEL__FINISHED_TEST)
                            text = text.format(START_DATE=campaign.start_date)
                            return user, text
                        # admission test: "принят"
                        elif user.admission_test.status == 'ACCEPTED':
                            text = translate(NodeTranslations.FUTURE_CLIENT__CAMPAIGN__CHANNEL__ACCEPTED_TEST)
                            text = text.format(START_DATE=campaign.start_date)
                            return user, text
                        #  admission test: "отказано"
                        elif user.admission_test.status == 'REJECTED':
                            return user, translate(NodeTranslations.FUTURE_CLIENT__CAMPAIGN__CHANNEL__REJECTED_TEST)
                    else:
                        text = translate(NodeTranslations.FUTURE_CLIENT__CAMPAIGN__NOT_CHANNEL)
                        text = text.format(START_DATE=campaign.start_date)
                        return user, text
                else:
                    # campaign привязан НЕ к ближайшей дате
                    if user.profile.communication_mode == 'CHANNEL':
                        text = translate(NodeTranslations.FUTURE_CLIENT__NOT_NEAREST__CHANNEL)
                        text = text.format(ADMISSION_START_DATE=campaign.admission_start_date)
                        return user, text
                    elif user.profile.communication_mode == 'CHAT':
                        text = translate(NodeTranslations.FUTURE_CLIENT__NOT_NEAREST__CHAT)
                        text = text.format(ADMISSION_START_DATE=campaign.admission_start_date)
                        return user, text
                    else:
                        raise ValueError(f'Expected channel or chat to be set on campaign {campaign.id}')

        else:
            # бывший участник
            if user.profile.is_in_club:
                return user, translate(NodeTranslations.FORMER_CLIENT__IS_IN_CLUB).format(USER_ID=user.profile.user_id)
            else:
                return user, translate(NodeTranslations.FORMER_CLIENT__IS_NOT_IN_CLUB).format(USER_ID=user.profile.user_id)

    raise NotImplementedError('please `check_user` function logic')
