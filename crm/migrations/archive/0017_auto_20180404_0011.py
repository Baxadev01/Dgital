# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-04-03 21:11


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0016_renewalrequest'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='renewalrequest',
            options={'verbose_name': '\u0437\u0430\u043f\u0440\u043e\u0441 \u043d\u0430 \u043f\u0440\u043e\u0434\u043b\u0435\u043d\u0438\u0435', 'verbose_name_plural': '\u0437\u0430\u043f\u0440\u043e\u0441\u044b \u043d\u0430 \u043f\u0440\u043e\u0434\u043b\u0435\u043d\u0438\u0435'},
        ),
        migrations.AddIndex(
            model_name='renewalrequest',
            index=models.Index(fields=['user'], name='crm_renewal_user_id_ad86bf_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalrequest',
            index=models.Index(fields=['request_type'], name='crm_renewal_request_93d743_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalrequest',
            index=models.Index(fields=['status'], name='crm_renewal_status_f6b9ff_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalrequest',
            index=models.Index(fields=['date_added'], name='crm_renewal_date_ad_454886_idx'),
        ),
    ]