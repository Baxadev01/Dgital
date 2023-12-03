from srbc.tgbot.actions import GoToNode, DefaultSendMessages, SaveTGMessage, GoToChosenNodeOrGoToNode, \
    LimitPerDayNotification, TimeoutRedirect
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode, BaseEndNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import TextInput, ChooseNodeOrGoNextNode, WorkDay, FloodControl, LimitPerDay

__all__ = ('QNothingFoundNode', 'QNothingFoundNodeRouterNode', 'QNothingFoundNodeInputNode')


@bot_manager.register(key=NodeNames.Q_NOTHING_FOUND)
class QNothingFoundNode(BaseNode):
    validators = [
        WorkDay(),
        FloodControl(message_type=SaveTGMessage.TYPE_QUESTION),
        LimitPerDay()
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_NOTHING_FOUND__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_NOTHING_FOUND_ROUTER)
class QNothingFoundNodeRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.Q_NOTHING_FOUND_INPUT)]


@bot_manager.register(key=NodeNames.Q_NOTHING_FOUND_INPUT)
class QNothingFoundNodeInputNode(BaseEndNode):
    validators = [TextInput()]
    handlers = [
        TimeoutRedirect(),
        SaveTGMessage(message_type=SaveTGMessage.TYPE_QUESTION),
        LimitPerDayNotification(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.MAIN_MENU_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_NOTHING_FOUND__SAVE_OK)]
