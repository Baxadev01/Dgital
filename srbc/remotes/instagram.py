# -*- coding: utf-8 -*-

import time
from datetime import datetime

import pytz
import requests

DELAY = 60


class InstagramServiceUnavailable(Exception):
    pass


class BadInstagramToken(Exception):
    pass


class InstagramManager:
    access_token = None

    def __init__(self, access_token):
        self.access_token = access_token

    def _exec_request(self, url, attempts=None, delay=None):
        """ Process request for the passed url.

        :param url:
        :type url: str | unicode
        :param attempts:
        :type attempts: int
        :param delay:
        :type delay: delay between attempts in seconds
        """
        attempts = attempts or 0
        delay = delay or DELAY

        response = requests.get(url)
        if response.status_code == 400:
            raise BadInstagramToken()
        elif response.status_code == 503:
            attempts -= 1
            if attempts >= 0:
                # sleep and try to get data again
                time.sleep(delay)
                return self._exec_request(url, attempts, delay)
            else:
                raise InstagramServiceUnavailable()
        else:
            return response.json()

    def get_user_info(self, attempts=None):
        ig_data_url = 'https://api.instagram.com/v1/users/self/?access_token=%s' % self.access_token

        ig_data = self._exec_request(ig_data_url, attempts=attempts)
        return ig_data.get('data', {})

    def get_posts(self, min_date=None, attempts=None):
        ig_page_url = 'https://api.instagram.com/v1/users/self/media/recent/?access_token=%s' % self.access_token

        last_post_hit = False

        while ig_page_url:
            ig_data = self._exec_request(ig_page_url, attempts=attempts)
            ig_page_url = ig_data.get('pagination', {}).get('next_url', None)
            posts = ig_data.get('data', [])

            for post in posts:
                post_date = datetime.fromtimestamp(int(post.get('created_time')), tz=pytz.UTC)
                if min_date and post_date <= min_date:
                    last_post_hit = True
                    break
                print("Post: #%s" % post.get('id'))
                yield post

            if last_post_hit:
                break
