# Generated by Django 3.1 on 2020-12-10 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0205_auto_20201123_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='stripesubscription',
            name='stripe_subscription_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
