from django.conf import settings

from srbc.tgbot.bot import bot_manager

botpolling_enabled = getattr(settings, 'ENABLE_BOTPOLLING', False)

if botpolling_enabled:
    from .nodes import *
