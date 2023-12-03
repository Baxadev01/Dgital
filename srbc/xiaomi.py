"""

request friends list:
curl -H 'Host: hm.mi-ae.com' -H 'Accept: */*' -H 'channel: appstore' -H 'appname: com.xiaomi.hm.health' -H 'apptoken: TQVBQFJyQktGHlp6QkpbRl5LRl5qek4uXAQABAAAAAKKsOJHU9H_VDWvHdnpCN2j_B49y_XlqO4ZRNgp0hq4b34Y_gfY4j9iBxvGLyY_tSRFxzi86N_pXeIlB0KYNhL-hq6_-oja8RUE8MloFAnjzRSZdpctnqmVi0WfBLvbWygNOtehMgJXF3OdumCjCQbo85RMTUQO1rX__-vCRElL70gbRvztctVeWWfFvnD_r8y-Vz6u0AurhBaXLSF2It9jdQU3NzuKiyxN5Rq6Sk2pAFvI3ZLVEs1vYr12SvCZ5Ww' -H 'Accept-Language: en-RU;q=1, ru-RU;q=0.9' -H 'cv: 39_2.4.3' -H 'lang: en' -H 'timezone: Europe/Moscow' -H 'appplatform: ios_phone' -H 'country: RU' -H 'v: 2.0' -H 'User-Agent: MiFit/2.4.3 (iPad; iOS 10.3; Scale/2.00)' --data 'appid=2882303761517276168&callid=1497172807626&cv=39_2.4.3&device=ios_10.3&device_type=ios_phone&lang=en&limit=10&start_uid=&stop_uid=&timezone=Europe/Moscow&userid=3011850871&v=1.0' --compressed 'https://hm.mi-ae.com/huami.health.band.userFriend.getFriendList.json?r=954C6A21-E638-403C-8EB4-353B93DBCBD5&t=1497172807626'


request friend stat:
curl -H 'Host: hm.mi-ae.com' -H 'Accept: */*' -H 'channel: appstore' -H 'appname: com.xiaomi.hm.health' -H 'apptoken: TQVBQFJyQktGHlp6QkpbRl5LRl5qek4uXAQABAAAAAKKsOJHU9H_VDWvHdnpCN2j_B49y_XlqO4ZRNgp0hq4b34Y_gfY4j9iBxvGLyY_tSRFxzi86N_pXeIlB0KYNhL-hq6_-oja8RUE8MloFAnjzRSZdpctnqmVi0WfBLvbWygNOtehMgJXF3OdumCjCQbo85RMTUQO1rX__-vCRElL70gbRvztctVeWWfFvnD_r8y-Vz6u0AurhBaXLSF2It9jdQU3NzuKiyxN5Rq6Sk2pAFvI3ZLVEs1vYr12SvCZ5Ww' -H 'Accept-Language: en-RU;q=1, ru-RU;q=0.9' -H 'cv: 39_2.4.3' -H 'lang: en' -H 'timezone: Europe/Moscow' -H 'appplatform: ios_phone' -H 'country: RU' -H 'v: 2.0' -H 'User-Agent: MiFit/2.4.3 (iPad; iOS 10.3; Scale/2.00)' --data "appid=2882303761517276168&callid=1497173176908&cv=39_2.4.3&device=ios_10.3&device_type=ios_phone&f_uid=3007877919&lang=en&limit=0&timezone=Europe/Moscow&userid=3011850871&v=1.0" --compressed 'https://hm.mi-ae.com/huami.health.band.userFriend.getUserFriendInfo.json?r=954C6A21-E638-403C-8EB4-353B93DBCBD5&t=1497173176907'


request user info:
curl -H 'Host: hm.mi-ae.com' -H 'Accept: */*' -H 'channel: appstore' -H 'appname: com.xiaomi.hm.health' -H 'apptoken: TQVBQFJyQktGHlp6QkpbRl5LRl5qek4uXAQABAAAAAAxuZs8byMHlMjv1DWyXVQZgRcxI-cXk6DmOs9EiMZN88D4C0qqOIvpH2V8T9IJhFmJ1wVCDV-YmkhSHtvEcvsDKwXS1-9J4UlXRfDDIJTTjZA6jUi34svLB3iaEkQ4gXHDTgeR-BmC_nxmo57paH1c1CdaYdl18rHdb2mntymWx_js_hFsVF8Quw3szwoIOSUSnhKA9e2UEVNazQnvg3dQsQI6D6q5BKj0pTlK3y5l2' -H 'Accept-Language: en-RU;q=1, ru-RU;q=0.9' -H 'cv: 39_2.4.3' -H 'lang: en' -H 'timezone: Europe/Moscow' -H 'appplatform: ios_phone' -H 'country: RU' -H 'v: 2.0' -H 'User-Agent: MiFit/2.4.3 (iPhone; iOS 10.3.2; Scale/2.00)' --data "appid=2882303761517276168&callid=1498539562653&cv=39_2.4.3&device=ios_10.3.2&device_type=ios_phone&lang=en&search_uid=3011850871&timezone=Europe/Moscow&userid=3007877919&v=1.0" --compressed 'https://hm.mi-ae.com/huami.health.band.userBasicInfo.searchUser.json?r=7FEEABFF-FEC8-43A3-AE22-9C69AD4FE4F3&t=1498539562651'

add user to friends:
curl -H 'Host: hm.mi-ae.com' -H 'Accept: */*' -H 'channel: appstore' -H 'appname: com.xiaomi.hm.health' -H 'apptoken: TQVBQFJyQktGHlp6QkpbRl5LRl5qek4uXAQABAAAAAAxuZs8byMHlMjv1DWyXVQZgRcxI-cXk6DmOs9EiMZN88D4C0qqOIvpH2V8T9IJhFmJ1wVCDV-YmkhSHtvEcvsDKwXS1-9J4UlXRfDDIJTTjZA6jUi34svLB3iaEkQ4gXHDTgeR-BmC_nxmo57paH1c1CdaYdl18rHdb2mntymWx_js_hFsVF8Quw3szwoIOSUSnhKA9e2UEVNazQnvg3dQsQI6D6q5BKj0pTlK3y5l2' -H 'Accept-Language: en-RU;q=1, ru-RU;q=0.9' -H 'cv: 39_2.4.3' -H 'lang: en' -H 'timezone: Europe/Moscow' -H 'appplatform: ios_phone' -H 'country: RU' -H 'v: 2.0' -H 'User-Agent: MiFit/2.4.3 (iPhone; iOS 10.3.2; Scale/2.00)' --data "appid=2882303761517276168&callid=1498539598604&cv=39_2.4.3&device=ios_10.3.2&device_type=ios_phone&lang=en&timezone=Europe/Moscow&to_uid=3011850871&userid=3007877919&v=1.0" --compressed 'https://hm.mi-ae.com/huami.health.band.pushMessage.sendInvitation.json?r=7FEEABFF-FEC8-43A3-AE22-9C69AD4FE4F3&t=1498539598604'
"""
import requests
from datetime import datetime, timedelta
from time import time
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class XiaomiManager(object, metaclass=Singleton):
    app_token = None
    app_token_expires = 0

    def get_token(self):
        if not self.app_token or not self.check_token_expire():
            ok = self.build_token()
            if not ok:
                return None

        return self.app_token

    def build_token(self):
        logger.info('Retrieving app token')
        self.app_token = ''

        url = 'http://account-us.huami.com/v1/client/app_tokens?app_name=com.xiaomi.hm.health&login_token=%s'
        url = url % settings.MIFIT_SETTINGS['login_token']

        ts = int(round(time() * 1000))

        response_data = requests.get(
            url=url,
            headers={
                "Accept-Language": "en-RU;q=1, ru-RU;q=0.9",
                "User-Agent": settings.MIFIT_SETTINGS['useragent'],
                "appplatform": "ios_phone",
                "callid": '%s' % ts,
                "country": "RU",
                "lang": "en",
                "timezone": "Europe/Moscow",
            },
            cookies={},
        )

        token_data = response_data.json()
        if 'error_code' in token_data:
            logger.info('Retrieving app token: FAIL')
            return False
        elif token_data.get('token_info'):
            logger.info('Retrieving app token: SUCCESS')
            token_data = token_data.get('token_info')
            self.app_token = token_data.get('app_token')
            self.app_token_expires = time() + token_data.get('app_ttl')
            logger.info('Xiaomi App token set valid until: %s' % self.app_token_expires)

        return True

    def check_token_expire(self):
        return time() < self.app_token_expires

    def post(self, url, data):
        if not self.check_token_expire():
            logger.info('App token expired')
            result = self.build_token()

            if not result:
                return None

        logger.info('Making XI-Api call to %s' % url)
        response_data = requests.post(
            url=url,
            data=data,
            headers={
                "Accept": "*/*",
                "Accept-Language": "en-RU;q=1, ru-RU;q=0.9",
                "Host": "hm.mi-ae.com",
                "User-Agent": settings.MIFIT_SETTINGS['useragent'],
                "appname": "com.xiaomi.hm.health",
                "appplatform": "ios_phone",
                "apptoken": self.app_token,
                "channel": "appstore",
                "country": "RU",
                "cv": settings.MIFIT_SETTINGS['cv'],
                "lang": "en",
                "timezone": "Europe/Moscow",
                "v": settings.MIFIT_SETTINGS['v']
            },
            cookies={},
        )

        response_data = response_data.json()

        logger.info(response_data)

        if 'error_code' in response_data:
            logger.info('Request result: FAIL')
            return self.post(url=url, data=data)
        else:
            return response_data
