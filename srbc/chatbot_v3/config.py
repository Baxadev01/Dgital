# -*- coding: utf-8 -*-
from srbc.chatbot_v3.constants import NodeTypes, NodeNames, messages

chat_bot_nodes = {
    NodeNames.START: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.MAIN_MENU: {
        'type': NodeTypes.MENU,
        'message': messages.MAIN_MENU,
        'items': [
            {'text': messages.Q, 'nextState': NodeNames.Q},
            {'text': messages.NODATA, 'nextState': NodeNames.NO_DATA},
            {'text': messages.DOC, 'nextState': NodeNames.DOC},
            {'text': messages.RENEW, 'nextState': NodeNames.RENEW},
            {'text': messages.DIARY, 'nextState': NodeNames.DIARY}
        ]
    },
    NodeNames.Q: {
        'type': NodeTypes.MENU,
        'message': messages.Q__TXT,
        'items': [
            {'text': messages.Q_TECH, 'nextState': NodeNames.Q_TECH_1},
            {'text': messages.Q_PROD, 'nextState': NodeNames.Q_PROD_1},
            {'text': messages.Q_DATA, 'nextState': NodeNames.Q_DATA},
            {'text': messages.Q_ANLZDIET, 'nextState': NodeNames.Q_DIET},
            {'text': messages.Q_THR, 'nextState': NodeNames.QTHR},
            {'text': messages.Q_HUN, 'nextState': NodeNames.Q_HUN},
            {'text': messages.Q_LRGPORT, 'nextState': NodeNames.Q_LRG_PORT},
            {'text': messages.Q_ORGDIET, 'nextState': NodeNames.Q_ORG_DIET},
            {'text': messages.Q_REGIME, 'nextState': NodeNames.Q_REGIME},
            {'text': messages.Q_RECOM, 'nextState': NodeNames.Q_RECOM}
        ]
    },
    NodeNames.Q_TECH_1: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_TECH__TXT_1,
        'nextState': NodeNames.Q_TECH_2
    },
    NodeNames.Q_TECH_2: {
        'type': NodeTypes.MENU,
        'message': messages.Q_TECH__TXT_2,
        'items': [
            {'text': messages.Q_TECH_YES, 'nextState': NodeNames.Q_TECH_YES},
            {'text': messages.Q_TECH_NO, 'nextState': NodeNames.Q_TECH_NO},
        ]
    },
    NodeNames.Q_TECH_YES: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_TECH_YES__TXT,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.Q_TECH_NO: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_TECH_NO__TXT,
        'nextState': NodeNames.Q_TECH_NO_INPUT
    },
    NodeNames.Q_TECH_NO_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.Q_TECH_NO_SAVE
    },
    NodeNames.Q_TECH_NO_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_TECH_NO__SAVE_OK,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.Q_PROD_1: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_PROD__TXT_1,
        'nextState': NodeNames.Q_PROD_2
    },
    NodeNames.Q_PROD_2: {
        'type': NodeTypes.MENU,
        'message': messages.Q_PROD__TXT_2,
        'items': [
            {'text': messages.Q_PROD_YES, 'nextState': NodeNames.Q_PROD_YES},
            {'text': messages.Q_PROD_NO, 'nextState': NodeNames.Q_PROD_NO},
        ]
    },
    NodeNames.Q_PROD_YES: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_PROD_YES__TXT,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.Q_PROD_NO: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_PROD_NO__TXT,
        'nextState': NodeNames.Q_PROD_NO_INPUT
    },
    NodeNames.Q_PROD_NO_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.Q_PROD_NO_SAVE
    },
    NodeNames.Q_PROD_NO_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_PROD_NO__SAVE_OK,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.Q_DATA: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_DATA__TXT,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.Q_DIET: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_ANLZDIET__TXT,
        'nextState': NodeNames.Q_DIET_INPUT
    },
    NodeNames.Q_DIET_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.Q_DIET_SAVE
    },
    NodeNames.Q_DIET_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_ANLZDIET__SAVE_OK_1,
        'nextState': NodeNames.Q_DIET_QUESTION_INPUT
    },
    NodeNames.Q_DIET_QUESTION_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.Q_DIET_QUESTION_SAVE
    },
    NodeNames.Q_DIET_QUESTION_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_ANLZDIET__SAVE_OK_2,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.QTHR: {
        'type': NodeTypes.MESSAGE,
        'message': messages.CHECK,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.Q_HUN: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_HUN__TXT,
        'nextState': NodeNames.Q_HUN_INPUT
    },
    NodeNames.Q_HUN_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.Q_HUN_SAVE
    },
    NodeNames.Q_HUN_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_HUN__SAVE_OK_1,
        'nextState': NodeNames.Q_HUN_QUESTION_INPUT
    },
    NodeNames.Q_HUN_QUESTION_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.Q_HUN_QUESTION_SAVE
    },
    NodeNames.Q_HUN_QUESTION_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_HUN__SAVE_OK_2,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.Q_LRG_PORT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_LRGPORT__TXT,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.Q_ORG_DIET: {
        'type': NodeTypes.MENU,
        'message': messages.Q_ORGDIET__TXT,
        'items': [
            {'text': messages.Q_ORGDIET_NOW, 'nextState': NodeNames.Q_ORG_DIET_NOW},
            {'text': messages.Q_ORGDIET_COND, 'nextState': NodeNames.Q_ORG_DIET_COND},
        ]
    },
    NodeNames.Q_ORG_DIET_NOW: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_ORGDIET_NOW__TXT1,
        'nextState': NodeNames.Q_ORG_DIET_NOW_INPUT
    },
    NodeNames.Q_ORG_DIET_NOW_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.Q_ORG_DIET_NOW_SAVE
    },
    NodeNames.Q_ORG_DIET_NOW_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_ORGDIET_NOW__TXT2,
        'nextState': NodeNames.Q_ORG_DIET_NOW_QUESTION_INPUT
    },
    NodeNames.Q_ORG_DIET_NOW_QUESTION_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.Q_ORG_DIET_QUESTION_SAVE
    },
    NodeNames.Q_ORG_DIET_COND: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_ORGDIET_COND__TXT,
        'nextState': NodeNames.Q_ORG_DIET_COND_QUESTION_INPUT
    },
    NodeNames.Q_ORG_DIET_COND_QUESTION_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.Q_ORG_DIET_QUESTION_SAVE
    },
    NodeNames.Q_ORG_DIET_QUESTION_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_ORGDIET__SAVE_OK,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.Q_REGIME: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_REGIME__TXT,
        'nextState': NodeNames.Q_REGIME_INPUT
    },
    NodeNames.Q_REGIME_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.Q_REGIME_SAVE
    },
    NodeNames.Q_REGIME_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_REGIME__SAVE_OK,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.Q_RECOM: {
        'type': NodeTypes.MENU,
        'message': messages.QRECOM_MENU,
        'items': [
            {'text': messages.Q_RECOM_WHY, 'nextState': NodeNames.Q_RECOM_WHY},
            {'text': messages.Q_RECOM_ANLZ, 'nextState': NodeNames.Q_RECOM_ANLZ},
            {'text': messages.Q_RECOM_IMPL, 'nextState': NodeNames.Q_RECOM_IMPL},
            {'text': messages.Q_RECOM_NOIMPL, 'nextState': NodeNames.Q_RECOM_NO_IMPL},
        ]
    },
    NodeNames.Q_RECOM_WHY: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_RECOM_WHY__TXT,
        'nextState': NodeNames.Q_RECOM
    },
    NodeNames.Q_RECOM_ANLZ: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_RECOM_ANLZ__TXT,
        'nextState': NodeNames.Q_RECOM
    },
    NodeNames.Q_RECOM_IMPL: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_RECOM_IMPL__TXT,
        'nextState': NodeNames.Q_RECOM
    },
    NodeNames.Q_RECOM_NO_IMPL: {
        'type': NodeTypes.MESSAGE,
        'message': messages.Q_RECOM_NOIMPL__TXT,
        'nextState': NodeNames.Q_RECOM
    },
    NodeNames.NO_DATA: {
        'type': NodeTypes.MESSAGE,
        'message': messages.NODATA__TXT,
        'nextState': NodeNames.START
    },
    NodeNames.DOC: {
        'type': NodeTypes.MESSAGE,
        'message': messages.DOC__TXT,
        'nextState': NodeNames.DOC_INPUT
    },
    NodeNames.DOC_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.DOC_SAVE
    },
    NodeNames.DOC_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.DOC__SAVE_OK,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.RENEW: {
        'type': NodeTypes.MENU,
        'message': messages.RENEW_MENU,
        'items': [
            {'text': messages.RENEW_CONT, 'nextState': NodeNames.RENEW_CONT},
            {'text': messages.RENEW_STOP, 'nextState': NodeNames.RENEW_STOP}
        ]
    },
    NodeNames.RENEW_CONT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.RENEW_CONT__TXT,
        'nextState': NodeNames.RENEW_CONT_INPUT
    },
    NodeNames.RENEW_CONT_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.RENEW_CONT_SAVE
    },
    NodeNames.RENEW_CONT_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.RENEW_CONT__SAVE_OK,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.RENEW_STOP: {
        'type': NodeTypes.MESSAGE,
        'message': messages.RENEW_STOP__TXT,
        'nextState': NodeNames.RENEW_STOP_INPUT
    },
    NodeNames.RENEW_STOP_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.RENEW_STOP_SAVE
    },
    NodeNames.RENEW_STOP_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.RENEW_STOP__SAVE_OK,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.DIARY: {
        'type': NodeTypes.MENU,
        'message': messages.DIARY__TXT,
        'items': [
            {'text': messages.DIARY_PUBLIC, 'nextState': NodeNames.DIARY_PUBLIC_INPUT},
            {'text': messages.DIARY_NOTPUBLIC, 'nextState': NodeNames.DIARY_NOT_PUBLIC_INPUT}
        ]
    },
    NodeNames.DIARY_PUBLIC_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.DIARY_PUBLIC_SAVE
    },
    NodeNames.DIARY_PUBLIC_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.DIARY_PUBLIC__SAVE_OK,
        'nextState': NodeNames.MAIN_MENU
    },
    NodeNames.DIARY_NOT_PUBLIC_INPUT: {
        'type': NodeTypes.MESSAGE,
        'message': messages.INPUT,
        'nextState': NodeNames.DIARY_NOT_PUBLIC_SAVE
    },
    NodeNames.DIARY_NOT_PUBLIC_SAVE: {
        'type': NodeTypes.MESSAGE,
        'message': messages.DIARY_NOTPUBLIC__SAVE_OK,
        'nextState': NodeNames.MAIN_MENU
    },
}
