from srbc.tgbot.config import NodeNames
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _


def get_keyboard(user):
    # node Q_RECOM_ANLZ will be shown for user if profile.warning_flag is in this list
    Q_RECOM_ANLZ_WARNING_FLAGS = ['TEST', 'OBSERVATION', 'DANGER', 'PR', 'OOC']

    result = [
        [TGRB(NodeNames.Q_RECOM_WHY)]
    ]

    if user.profile.warning_flag in Q_RECOM_ANLZ_WARNING_FLAGS:
        result.append([TGRB(NodeNames.Q_RECOM_ANLZ)])

    if user.profile.has_full_bot_access:
        result.append([TGRB(NodeNames.Q_RECOM_IMPL)])

    result.append([TGRB(NodeNames.Q_RECOM_NOIMPL)])
    result.append([TGRB(NodeNames.BACK_TO_MAIN_MENU)])

    return result
