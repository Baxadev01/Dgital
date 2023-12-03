# -*- coding: utf-8 -*-

from datetime import date

import factory
from django.utils import timezone

from crm.models import Application
from srbc.models import Checkpoint, User, Profile, Wave, ParticipationGoal, DiaryRecord


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'username_%d' % n)
    profile = factory.RelatedFactory('srbc.tests.factories.ProfileFactory', 'user')
    application = factory.RelatedFactory('srbc.tests.factories.ApplicationFactory', 'user')


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Application


class WaveFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Wave

    title = factory.Sequence(lambda n: 'title_%d' % n)
    start_date = date.today()


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory, profile=None)
    wave = factory.SubFactory(WaveFactory)


class CheckpointFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Checkpoint


class DiaryRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DiaryRecord


class ParticipationGoalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ParticipationGoal

    status_changed_on = timezone.now()
    ordernum = factory.Sequence(lambda n: n)
