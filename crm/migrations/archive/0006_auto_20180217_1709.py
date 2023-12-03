# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-02-17 14:09


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('crm', '0005_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscountCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
                ('expiring_at', models.DateTimeField(blank=True, null=True)),
                ('is_applied', models.BooleanField(default=False)),
                ('applied_at', models.DateTimeField(blank=True, null=True)),
                ('dicount_percent', models.DecimalField(decimal_places=4, max_digits=8)),
                ('payment_type', models.CharField(blank=True, choices=[(b'CLUB', '\u041e\u043f\u043b\u0430\u0442\u0430 \u0443\u0447\u0430\u0441\u0442\u0438\u044f \u0432 \u043a\u043b\u0443\u0431\u0435'), (b'CHANNEL', '\u041e\u043f\u043b\u0430\u0442\u0430 \u0443\u0447\u0430\u0441\u0442\u0438\u044f \u0432 \u043c\u0430\u0440\u0430\u0444\u043e\u043d\u0435 (\u0437\u0430\u043e\u0447\u043d\u044b\u0439)'), (b'CHAT', '\u041e\u043f\u043b\u0430\u0442\u0430 \u0443\u0447\u0430\u0441\u0442\u0438\u044f \u0432 \u043c\u0430\u0440\u0430\u0444\u043e\u043d\u0435 (\u043e\u0447\u043d\u044b\u0439)')], max_length=20, null=True)),
                ('days_paid', models.IntegerField()),
                ('applied_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='effective_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_type',
            field=models.CharField(choices=[(b'CLUB', '\u041e\u043f\u043b\u0430\u0442\u0430 \u0443\u0447\u0430\u0441\u0442\u0438\u044f \u0432 \u043a\u043b\u0443\u0431\u0435'), (b'CHANNEL', '\u041e\u043f\u043b\u0430\u0442\u0430 \u0443\u0447\u0430\u0441\u0442\u0438\u044f \u0432 \u043c\u0430\u0440\u0430\u0444\u043e\u043d\u0435 (\u0437\u0430\u043e\u0447\u043d\u044b\u0439)'), (b'CHAT', '\u041e\u043f\u043b\u0430\u0442\u0430 \u0443\u0447\u0430\u0441\u0442\u0438\u044f \u0432 \u043c\u0430\u0440\u0430\u0444\u043e\u043d\u0435 (\u043e\u0447\u043d\u044b\u0439)')], default='YA', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[(b'PENDING', '\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u043e\u043f\u043b\u0430\u0442\u044b'), (b'APPROVED', '\u041e\u043f\u043b\u0430\u0447\u0435\u043d'), (b'CANCELED', '\u041e\u0442\u043c\u0435\u043d\u0435\u043d')], default=b'PENDING', max_length=100),
        ),
        migrations.AddField(
            model_name='order',
            name='discount_code',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='crm.DiscountCode'),
        ),
    ]
