# -*- coding: utf-8 -*-

from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.utils import translate as _
from .base import RouterNode, BaseEndNode

__all__ = ('MainMenuNode', 'BackToMainMenuNode', 'MainMenuRouterNode',)


@bot_manager.register(key=NodeNames.MAIN_MENU)
class MainMenuNode(BaseEndNode):

    def get_messages(self):
        return [_(NodeTranslations.MAIN_MENU__TXT)]


@bot_manager.register(key=NodeNames.BACK_TO_MAIN_MENU)
class BackToMainMenuNode(MainMenuNode):

    def get_messages(self):
        return [_(NodeTranslations.BACK_TO_MAIN_MENU__TXT)]


@bot_manager.register(key=NodeNames.MAIN_MENU_ROUTER)
class MainMenuRouterNode(RouterNode):
    pass
