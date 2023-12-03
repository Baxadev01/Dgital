# -*- coding: utf-8 -*-
import uuid
import hashlib
import mailchimp3
from django.conf import settings
from requests import HTTPError
from crm.models import Campaign, UserAdmissionTest
from django.db.models.signals import pre_save
from django.utils import timezone


class MailchimpClient:
    client = None

    def __init__(self):
        self.client = mailchimp3.MailChimp(settings.MAILCHIMP_USERNAME, settings.MAILCHIMP_API_KEY)

    def find_member(self, email):
        try:
            mc_user = self.client.lists.members.get(settings.MAILCHIMP_LIST_ID, self.get_hash(email))
        except HTTPError as e:
            mc_user = None

        return mc_user

    def add_member(self, userinfo):

        mc_user = self.client.lists.members.create_or_update(
            list_id=settings.MAILCHIMP_LIST_ID,
            subscriber_hash=self.get_hash(userinfo.email),
            data={
                'email_address': userinfo.email,
                'status': 'pending',
                'status_if_new': 'pending',
                'merge_fields': {
                    'FNAME': userinfo.first_name,
                    'LNAME': userinfo.last_name,
                }
            }
        )

        return mc_user

    def set_test_status(self, userinfo, status):
        if status in settings.MAILCHIMP_TEST_STATUS:
            mc_user = self.client.lists.members.update(
                list_id=settings.MAILCHIMP_LIST_ID,
                subscriber_hash=self.get_hash(userinfo.email),
                data={
                    'interests': {
                        settings.MAILCHIMP_TEST_STATUS[status]: True
                    }
                }
            )

            return mc_user

    def set_communication_mode(self, userinfo, mode):
        mc_user = self.client.lists.members.update(
            list_id=settings.MAILCHIMP_LIST_ID,
            subscriber_hash=self.get_hash(userinfo.email),
            data={
                'interests': {
                    settings.MAILCHIMP_COMMUNICATION_GROUP_IDS['CHAT']: mode == 'CHAT',
                    settings.MAILCHIMP_COMMUNICATION_GROUP_IDS['CHANNEL']: mode == 'CHANNEL',
                }
            }
        )

        return mc_user

    def set_campaign(self, userinfo, campaign_id):
        campaigns_list = Campaign.objects.filter(mailchimp_group_id__isnull=False).all()

        campaigns_dict = {campaign.mailchimp_group_id: campaign.pk == campaign_id for campaign in campaigns_list}
        # print "\n" * 2
        # print campaigns_dict
        # print "\n" * 2

        mc_user = self.client.lists.members.update(
            list_id=settings.MAILCHIMP_LIST_ID,
            subscriber_hash=self.get_hash(userinfo.email),
            data={
                'interests': campaigns_dict
            }
        )

        return mc_user

    @staticmethod
    def get_hash(email):
        m = hashlib.md5()
        m.update(email.lower())
        return m.hexdigest()


# def manage_admission_time(sender, instance, **kwargs):
#     chimp = MailchimpClient()
#
#     if instance.status in ['DONE'] and instance.completed_date is None:
#         instance.completed_date = timezone.now()
#     if instance.status in ['PASSED', 'FAILED'] and instance.reviewed_date is None:
#         instance.reviewed_date = timezone.now()
#
#     chimp.set_test_status(instance.user, instance.status)
#
#
# pre_save.connect(manage_admission_time, sender=UserAdmissionTest)
