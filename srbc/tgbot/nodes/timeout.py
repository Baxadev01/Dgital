# -*- coding: utf-8 -*-

from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.actions import DefaultSendMessages, GoToNode, PreSaveMessage
from srbc.tgbot.utils import translate as _
from .base import BaseEndNode, BaseNode


__all__ = ('BackToMainMenuByTimeoutNode',)


@bot_manager.register(key=NodeNames.BACK_TO_MAIN_MENU_BY_TIMEOUT)
class BackToMainMenuByTimeoutNode((BaseEndNode)):

    handlers = [
        PreSaveMessage(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.MAIN_MENU_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.BACK_TO_MAIN_MENU_BY_TIMEOUT__TXT)]

