# Generated by Django 3.0.6 on 2020-05-30 10:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('support', '0001_initial'), ('support', '0002_auto_20170715_2215'), ('support', '0003_ticket_signature'), ('support', '0004_auto_20170715_2246'), ('support', '0005_auto_20170715_2252'), ('support', '0006_auto_20170718_0558'), ('support', '0007_auto_20200321_1033')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.CharField(default='', max_length=512)),
                ('subject', models.TextField(max_length=100)),
                ('body', models.TextField()),
                ('status', models.CharField(blank=True, choices=[(b'NEW', 'Новый'), (b'ASSIGNED', 'В работе'), (b'RESOLVED', 'Отвечен'), (b'REJECTED', 'Отклонен')], default=b'NEW', max_length=20)),
                ('posted_at', models.DateTimeField(auto_now_add=True)),
                ('assignee', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_tickets', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to=settings.AUTH_USER_MODEL)),
                ('full_name', models.CharField(default='', max_length=512)),
                ('signature', models.CharField(default='', max_length=64)),
            ],
        ),
        migrations.AddIndex(
            model_name='ticket',
            index=models.Index(fields=['signature'], name='support_tic_signatu_80b690_idx'),
        ),
        migrations.AddIndex(
            model_name='ticket',
            index=models.Index(fields=['posted_at'], name='support_tic_posted__54b954_idx'),
        ),
        migrations.AddIndex(
            model_name='ticket',
            index=models.Index(fields=['assignee'], name='support_tic_assigne_d963a3_idx'),
        ),
        migrations.AddIndex(
            model_name='ticket',
            index=models.Index(fields=['status'], name='support_tic_status_363e60_idx'),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='assignee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_tickets', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='assignee',
            field=models.ForeignKey(blank=True, limit_choices_to={'groups__name': 'Feedback Manager'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_tickets', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='status',
            field=models.CharField(blank=True, choices=[('NEW', 'Новый'), ('ASSIGNED', 'В работе'), ('RESOLVED', 'Отвечен'), ('REJECTED', 'Отклонен')], default='NEW', max_length=20),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tickets', to=settings.AUTH_USER_MODEL),
        ),
    ]