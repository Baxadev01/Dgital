# Generated by Django 3.1 on 2020-11-23 08:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0205_auto_20201123_1139'),
        ('crm', '0017_auto_20201110_0851'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripePayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_id', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='payment',
            name='subscription',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='srbc.subscription'),
        ),
        migrations.AlterField(
            model_name='tariffhistory',
            name='tariff',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tariff_history', to='srbc.tariff'),
        ),
        migrations.AddField(
            model_name='payment',
            name='stripe_payment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.stripepayment'),
        ),
    ]
