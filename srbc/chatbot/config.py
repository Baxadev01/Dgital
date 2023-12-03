# -*- coding: utf-8 -*-

from srbc.chatbot.filters import (
    UserCommunicationMode, WorkDay, LimitPerDay,
    RenewalIsPossible, FloodControl, MessageLength
)
from srbc.chatbot.messages import bot_messages

chatbot_tags_to_process = {
    "#япродолжаю": {
        "tag": "#япродолжаю",
        "actions": [
            {
                "action": "renewal",
                "params": {
                    "flag": "POSITIVE",
                },
            },
            {
                "action": "note",
                "params": {
                    "label": "NB",
                },
            },
        ],
        "checks": [
            {
                "class": UserCommunicationMode,
                "params": {
                    "communication_mode": "CHANNEL",
                },
            },
            {
                "class": MessageLength,
                "params": {
                    "min": 20
                },

            },
            {
                "class": RenewalIsPossible,
            },
        ],
    },
    "#янепродолжаю": {
        "tag": "#янепродолжаю",
        "actions": [
            {
                "action": "renewal",
                "params": {
                    "flag": "NEGATIVE",
                },
            },
            {
                "action": "note",
                "params": {
                    "label": "NB",
                },
            },
        ],
        "checks": [
            {
                "class": UserCommunicationMode,
                "params": {
                    "communication_mode": "CHANNEL",
                },
            },
            {
                "class": MessageLength,
                "params": {
                    "min": 20,
                },

            },
            {
                "class": RenewalIsPossible,
            },

        ],

    },
    "#обследование": {
        "tag": "#обследование",
        "actions": [
            {
                "action": "note",
                "params": {
                    "label": "DOC",
                    "raise_alarm": True,
                },
            },
            {
                "action": "reply",
                "params": {
                    "message": bot_messages.message_accepted_doc,
                },
            },
        ],
        "checks": [
            {
                "class": MessageLength,
                "params": {
                    "min": 20
                },

            },
            {
                "class": WorkDay,
            },
        ],
    },
    "#away": {
        "tag": "#away",
        "actions": [
            {
                "action": "note",
                "params": {
                    "label": "NB",
                    "raise_alarm": True,
                },
            },
            {
                "action": "reply",
                "params": {
                    "message": bot_messages.message_accepted_away,
                },
            },
        ],
        "checks": [
            {
                "class": MessageLength,
                "params": {
                    "min": 20
                },

            },
            {
                "class": WorkDay,
            },
        ],

    },
    "#формула": {
        "tag": "#формула",
        "actions": [
            {
                "action": "manual",
                "params": {
                    "folder": "FORMULA",
                },
            },
            {
                "action": "reply",
                "params": {
                    "message": bot_messages.message_recorded_response_pending,
                },
            },

        ],
        "checks": [
            {
                "class": UserCommunicationMode,
                "params": {
                    "communication_mode": "CHANNEL",
                },
            },
            {
                "class": WorkDay,
            },
            {
                "class": MessageLength,
                "params": {
                    "min": 20
                },

            },
            {
                "class": FloodControl,
                "params": {
                    "timeout": 60,
                    "message_type": "FORMULA",
                },

            },
        ],
    },
    "#вопрос": {
        "tag": "#вопрос",
        "actions": [
            {
                "action": "manual",
                "params": {
                    "folder": "QUESTION",
                },
            },
            {
                "action": "reply",
                "params": {
                    "message": bot_messages.message_recorded_response_pending,
                },
            },

        ],
        "checks": [
            {
                "class": UserCommunicationMode,
                "params": {
                    "communication_mode": "CHANNEL",
                },
            },
            {
                "class": WorkDay,
            },
            {
                "class": MessageLength,
                "params": {
                    "min": 20,
                },

            },
            {
                "class": FloodControl,
                "params": {
                    "timeout": 60,
                    "message_type": "QUESTION",
                },

            },
            {
                "class": LimitPerDay,
                "params": {
                    "limit": 5,
                    "limit_soft": 3,
                    "message_type": "QUESTION",
                },
            },
        ],
    },
    "#дневник": {
        "tag": "#дневник",
        "actions": [
            {
                "action": "manual",
                "params": {
                    "folder": "FEEDBACK",
                },
            },
            {
                "action": "blog",
                "params": {
                    "is_private": False,
                },
            },
            {
                "action": "reply",
                "params": {
                    "message": bot_messages.message_accepted_diary,
                },
            },

        ],
        "checks": [
            {
                "class": UserCommunicationMode,
                "params": {
                    "communication_mode": "CHANNEL",
                },
            },
            {
                "class": FloodControl,
                "params": {
                    "timeout": 60,
                    "message_type": "FEEDBACK",
                },

            },
            {
                "class": WorkDay,
            },
        ],
    },
    "#дневникличное": {
        "tag": "#дневникличное",
        "actions": [
            {
                "action": "manual",
                "params": {
                    "folder": "FEEDBACK",
                },
            },
            {
                "action": "blog",
                "params": {
                    "is_private": True,
                },
            },
            {
                "action": "reply",
                "params": {
                    "message": bot_messages.message_accepted_diaryprivate,
                },
            },

        ],
        "checks": [
            {
                "class": UserCommunicationMode,
                "params": {
                    "communication_mode": "CHANNEL",
                },
            },
            {
                "class": FloodControl,
                "params": {
                    "timeout": 60,
                    "message_type": "FEEDBACK",
                },

            },

            {
                "class": WorkDay,
            },
        ],
    },

}
