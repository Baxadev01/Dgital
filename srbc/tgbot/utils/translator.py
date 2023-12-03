# -*- coding: utf-8 -*-

import logging
import typing as ty

from content.models import TGTranslation
from srbc.tgbot.config import NodeTranslations

__all__ = ('translate', 'rebuild_translations')

logger = logging.getLogger(__name__)


class Translator(object):

    def __init__(self):
        self.translations: ty.Dict = {}

    def fill_translations(self):
        if self.translations:
            self.translations = {}

        for key in dir(NodeTranslations):
            if (not key.isupper()) or key.endswith('_ROUTER'):
                continue
            self.translations[key] = self._get_translation_from_db(key=key)

    @staticmethod
    def _get_translation_from_db(key: str) -> str:
        try:
            translation = TGTranslation.objects.values_list('translation').get(key=key)
        except TGTranslation.DoesNotExist:
            logger.error('Translation not found for key [%s]' % key)
            raise ValueError
            # translation = key.replace('_', ' ')
        else:
            translation = translation[0]
        return translation

    def translate(self, key):
        if not self.translations:
            self.fill_translations()

        return self.translations[key]


translator = Translator()


def translate(key):
    return translator.translate(key=key)


def rebuild_translations():
    translator.fill_translations()
