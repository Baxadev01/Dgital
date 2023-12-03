# Generated by Django 3.0.6 on 2020-05-30 12:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields
import markdownx.models
import shared.models


class Migration(migrations.Migration):

    replaces = [('crm', '0010_auto_20180223_0840'), ('crm', '0011_auto_20180225_1812'), ('crm', '0012_auto_20180305_0936'), ('crm', '0013_auto_20180318_1630'), ('crm', '0014_application_is_payment_special'), ('crm', '0015_auto_20180330_0137'), ('crm', '0016_renewalrequest'), ('crm', '0017_auto_20180404_0011'), ('crm', '0018_renewalrequest_payment_special'), ('crm', '0019_auto_20180404_0958'), ('crm', '0020_billingtransaction_tariff'), ('crm', '0021_renewalrequest_usernote'), ('crm', '0022_auto_20180419_1323'), ('crm', '0023_auto_20180502_1430'), ('crm', '0023_auto_20180430_1614'), ('crm', '0024_merge_20180516_1526'), ('crm', '0025_auto_20180730_1808'), ('crm', '0026_auto_20180921_1247'), ('crm', '0027_telegrammailtemplate'), ('crm', '0028_auto_20190119_1227'), ('crm', '0029_application_country'), ('crm', '0030_auto_20190119_1245'), ('crm', '0031_remove_campaign_is_admission_open'), ('crm', '0032_remove_campaign_is_open'), ('crm', '0033_application_goal_weight'), ('crm', '0034_auto_20190121_1248'), ('crm', '0035_auto_20190121_1431'), ('crm', '0036_auto_20190805_1433'), ('crm', '0037_auto_20200122_0621'), ('crm', '0038_auto_20200321_1033')]

    dependencies = [
        ('srbc', '0142_auto_20180318_1623'),
        ('content', '0059_auto_20180318_1623'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('srbc', '0161_auto_20180408_1213'),
        ('crm', '0009_order_wave'),
        ('srbc', '0247_auto_20190805_1433'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[(b'PENDING', 'Ожидает оплаты'), (b'PROCESSING', 'В обработке'), (b'APPROVED', 'Оплачен'), (b'CANCELED', 'Отменен')], default=b'PENDING', max_length=100),
        ),
        migrations.AlterModelOptions(
            name='order',
            options={'verbose_name': 'Счёт', 'verbose_name_plural': 'Счета'},
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_provider',
            field=models.CharField(blank=True, choices=[(b'YA', 'Яндекс-Касса'), (b'PP', 'PayPal'), (b'MANUAL', 'Вручную')], default=b'YA', max_length=100, null=True),
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='AdmissionTestQuestion',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('text', markdownx.models.MarkdownxField()),
                        ('is_active', models.BooleanField(default=False)),
                        ('answer_ok', models.BooleanField(default=False, verbose_name='Соответствует методичке')),
                        ('answer_sweet', models.BooleanField(default=False, verbose_name='Сладкое натощак')),
                        ('answer_interval', models.BooleanField(default=False, verbose_name='Нарушены интервалы')),
                        ('answer_protein', models.BooleanField(default=False, verbose_name='Недостаток белка')),
                        ('answer_carb', models.BooleanField(default=False, verbose_name='Неверное количество углеводов')),
                        ('answer_fat', models.BooleanField(default=False, verbose_name='Превышение жирности')),
                        ('answer_weight', models.BooleanField(default=False, verbose_name='Неверные навески')),
                    ],
                ),
                migrations.CreateModel(
                    name='Application',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('gender', models.CharField(choices=[(b'M', 'Мужской'), (b'F', 'Женский')], default=b'F', max_length=1, verbose_name='Пол')),
                        ('is_payment_allowed', models.BooleanField(default=False, verbose_name='Разрешена оплата')),
                        ('first_name', models.CharField(max_length=100, verbose_name='Имя')),
                        ('last_name', models.CharField(max_length=100, verbose_name='Фамилия')),
                        ('email', models.EmailField(max_length=254, verbose_name='Электронная почта')),
                        ('email_status', models.CharField(blank=True, choices=[(b'NEW', 'Новый'), (b'PENDING', 'Ожидает подтверждения'), (b'APPROVED', 'Подтвержден'), (b'DISCONNECTED', 'Отписан')], default=b'NEW', max_length=25)),
                        ('phone', models.CharField(blank=True, max_length=100, null=True, verbose_name='Номер мобильного телефона')),
                        ('country', models.CharField(max_length=100, null=True, verbose_name='Страна')),
                        ('city', models.CharField(max_length=100, null=True, verbose_name='Город')),
                        ('height', models.IntegerField(null=True, verbose_name='Ваш рост')),
                        ('weight', shared.models.DecimalRangeField(decimal_places=3, max_digits=8, null=True, verbose_name='Ваш текущий (стартовый) вес')),
                        ('age', models.IntegerField(blank=True, null=True, verbose_name='Ваш возраст')),
                        ('birth_year', models.IntegerField(null=True, verbose_name='Год рождения')),
                        ('sickness', models.TextField(null=True, verbose_name='Имеющиеся заболевания')),
                        ('goals', models.TextField(null=True, verbose_name='Цели на марафон')),
                        ('need_tracker', models.BooleanField(default=False, verbose_name='Хочу фитнесс-трекер')),
                        ('is_approved', models.BooleanField(default=False, verbose_name='Анкета проверена')),
                        ('social_acc_status', models.CharField(blank=True, choices=[(b'PENDING', 'Ожидает подтверждения'), (b'APPROVED', 'Подтвержден'), (b'SUSPICIOUS', 'Подозрительный'), (b'REJECTED', 'Отклонён')], default=b'PENDING', max_length=25)),
                        ('admission_status', models.CharField(blank=True, choices=[(b'NOT_STARTED', 'Не дошел'), (b'IN_PROGRESS', 'В процессе'), (b'DONE', 'Завершил'), (b'PASSED', 'Проверено, всё ок'), (b'FAILED', 'Проверено, завалил'), (b'REJECTED', 'Отказано'), (b'ACCEPTED', 'Принят')], default=b'NOT_STARTED', max_length=100)),
                        ('tos_signed_date', models.DateTimeField(blank=True, null=True)),
                        ('active_payment_order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.Order')),
                        ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='crm.Campaign')),
                        ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='application', to=settings.AUTH_USER_MODEL)),
                    ],
                ),
                migrations.CreateModel(
                    name='UserAdmissionTest',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('status', models.CharField(blank=True, choices=[(b'NOT_STARTED', 'Не дошел'), (b'IN_PROGRESS', 'В процессе'), (b'DONE', 'Завершил'), (b'PASSED', 'Проверено, всё ок'), (b'FAILED', 'Проверено, завалил'), (b'REJECTED', 'Отказано'), (b'ACCEPTED', 'Принят')], default=b'NOT_STARTED', max_length=100)),
                        ('question_asked', models.TextField(blank=True, null=True)),
                        ('recommendation_info', models.TextField(blank=True, null=True, verbose_name='Информация о рекоммендателе')),
                        ('started_date', models.DateTimeField(auto_now_add=True)),
                        ('completed_date', models.DateTimeField(blank=True, null=True)),
                        ('reviewed_date', models.DateTimeField(blank=True, null=True)),
                        ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admission_test', to=settings.AUTH_USER_MODEL)),
                    ],
                ),
                migrations.CreateModel(
                    name='UserAdmissionTestQuestion',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('question_num', models.SmallIntegerField()),
                        ('is_answered', models.BooleanField(default=False)),
                        ('text', markdownx.models.MarkdownxField()),
                        ('answer_ok', models.BooleanField(default=False, verbose_name='Соответствует методичке')),
                        ('answer_ok_comment', models.TextField(blank=True, null=True)),
                        ('answer_sweet', models.BooleanField(default=False, verbose_name='Сладкое натощак')),
                        ('answer_sweet_comment', models.TextField(blank=True, null=True)),
                        ('answer_interval', models.BooleanField(default=False, verbose_name='Нарушены интервалы')),
                        ('answer_interval_comment', models.TextField(blank=True, null=True)),
                        ('answer_protein', models.BooleanField(default=False, verbose_name='Недостаток белка')),
                        ('answer_protein_comment', models.TextField(blank=True, null=True)),
                        ('answer_carb', models.BooleanField(default=False, verbose_name='Неверное количество углеводов')),
                        ('answer_carb_comment', models.TextField(blank=True, null=True)),
                        ('answer_fat', models.BooleanField(default=False, verbose_name='Превышение жирности')),
                        ('answer_fat_comment', models.TextField(blank=True, null=True)),
                        ('answer_weight', models.BooleanField(default=False, verbose_name='Неверные навески')),
                        ('answer_weight_comment', models.TextField(blank=True, null=True)),
                        ('admission_test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='crm.UserAdmissionTest')),
                        ('source_question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_usage', to='crm.AdmissionTestQuestion')),
                    ],
                    options={
                        'ordering': ['admission_test', 'question_num'],
                    },
                ),
                migrations.AddIndex(
                    model_name='useradmissiontestquestion',
                    index=models.Index(fields=['is_answered'], name='crm_useradm_is_answ_6808ea_idx'),
                ),
                migrations.AddIndex(
                    model_name='useradmissiontestquestion',
                    index=models.Index(fields=['admission_test'], name='crm_useradm_admissi_9191b1_idx'),
                ),
                migrations.AddIndex(
                    model_name='useradmissiontestquestion',
                    index=models.Index(fields=['source_question'], name='crm_useradm_source__dac47c_idx'),
                ),
                migrations.AddIndex(
                    model_name='useradmissiontest',
                    index=models.Index(fields=['user'], name='crm_useradm_user_id_63b73c_idx'),
                ),
                migrations.AddIndex(
                    model_name='useradmissiontest',
                    index=models.Index(fields=['status'], name='crm_useradm_status_11a323_idx'),
                ),
                migrations.AddIndex(
                    model_name='application',
                    index=models.Index(fields=['user'], name='crm_applica_user_id_6b1984_idx'),
                ),
                migrations.AddIndex(
                    model_name='application',
                    index=models.Index(fields=['need_tracker'], name='crm_applica_need_tr_9fc937_idx'),
                ),
                migrations.AddIndex(
                    model_name='application',
                    index=models.Index(fields=['is_approved'], name='crm_applica_is_appr_1fc7e9_idx'),
                ),
            ],
        ),
        migrations.AddField(
            model_name='application',
            name='is_payment_special',
            field=models.BooleanField(default=False, verbose_name='Особые условия оплаты'),
        ),
        migrations.AlterField(
            model_name='application',
            name='goals',
            field=models.TextField(null=True, verbose_name='Цели на проекте'),
        ),
        migrations.AlterField(
            model_name='discountcode',
            name='payment_type',
            field=models.CharField(blank=True, choices=[(b'CLUB', 'Оплата участия в клубе'), (b'CHANNEL', 'Оплата участия в проекте (заочный)'), (b'CHAT', 'Оплата участия в проекте (очный)')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_type',
            field=models.CharField(choices=[(b'CLUB', 'Оплата участия в клубе'), (b'CHANNEL', 'Оплата участия в проекте (заочный)'), (b'CHAT', 'Оплата участия в проекте (очный)')], max_length=100),
        ),
        migrations.CreateModel(
            name='RenewalRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_type', models.CharField(choices=[(b'POSITIVE', '#япродолжаю'), (b'NEGATIVE', '#яНЕпродолжаю')], max_length=10, verbose_name='Хэштег')),
                ('comment', models.TextField(verbose_name='Отзыв')),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(blank=True, choices=[(b'NEW', 'Новый'), (b'PREACCEPTED', 'Предварительно одобрен'), (b'TBD', 'Требуется согласование'), (b'REJECTED', 'Отклонен'), (b'ACCEPTED', 'Одобрен')], default=b'NEW', max_length=25)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'запрос на продление',
                'verbose_name_plural': 'запросы на продление',
            },
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
        migrations.AddField(
            model_name='renewalrequest',
            name='payment_special',
            field=models.BooleanField(default=False, verbose_name='Особые условия оплаты'),
        ),
        migrations.AddField(
            model_name='renewalrequest',
            name='comment_internal',
            field=models.TextField(blank=True, default=b'', verbose_name='Служебная заметка'),
        ),
        migrations.AlterField(
            model_name='renewalrequest',
            name='status',
            field=models.CharField(blank=True, choices=[(b'NEW', 'Новый'), (b'PENDING', 'Ожидает ответа участника'), (b'PREACCEPTED', 'Предварительно одобрен'), (b'TBD', 'Требуется согласование'), (b'REJECTED', 'Отклонен'), (b'ACCEPTED', 'Одобрен')], default=b'NEW', max_length=25),
        ),
        migrations.AddField(
            model_name='renewalrequest',
            name='usernote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='srbc.UserNote'),
        ),
        migrations.AddField(
            model_name='order',
            name='last_updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='order',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='application',
            name='height',
            field=models.IntegerField(null=True, verbose_name='Ваш рост, в см'),
        ),
        migrations.AlterField(
            model_name='application',
            name='weight',
            field=shared.models.DecimalRangeField(decimal_places=3, max_digits=8, null=True, verbose_name='Ваш текущий (стартовый) вес, в кг'),
        ),
        migrations.AlterField(
            model_name='application',
            name='height',
            field=models.IntegerField(null=True, verbose_name='Ваш рост, в см'),
        ),
        migrations.AlterField(
            model_name='application',
            name='weight',
            field=shared.models.DecimalRangeField(decimal_places=3, max_digits=8, null=True, verbose_name='Ваш текущий (стартовый) вес, в кг'),
        ),
        migrations.AlterField(
            model_name='order',
            name='wave',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wave_to_join', to='srbc.Wave', verbose_name='Payment wave'),
        ),
        migrations.CreateModel(
            name='TelegramMailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('slug', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('text', markdownx.models.MarkdownxField(blank=True, default=b'', null=True)),
            ],
        ),
        migrations.RenameField(
            model_name='application',
            old_name='country',
            new_name='country_old',
        ),
        migrations.AddField(
            model_name='application',
            name='country',
            field=django_countries.fields.CountryField(max_length=2, verbose_name='Страна'),
        ),
        migrations.RemoveField(
            model_name='campaign',
            name='is_admission_open',
        ),
        migrations.RemoveField(
            model_name='campaign',
            name='is_open',
        ),
        migrations.AddField(
            model_name='application',
            name='goal_weight',
            field=shared.models.DecimalRangeField(decimal_places=3, max_digits=8, null=True, verbose_name='Целевой вес'),
        ),
        migrations.AddField(
            model_name='application',
            name='baby_birthdate',
            field=models.DateField(blank=True, null=True, verbose_name='Дата рождения ребёнка'),
        ),
        migrations.AddField(
            model_name='application',
            name='baby_case',
            field=models.CharField(choices=[(b'PREGNANT', 'Беременность'), (b'FEEDING', 'Кормление грудью'), (b'NONE', 'Ничего из перечисленного')], default=b'NONE', max_length=100, verbose_name='Особый случай'),
        ),
        migrations.AddField(
            model_name='order',
            name='tariff',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='srbc.Tariff'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['payment_provider'], name='crm_order_payment_94f232_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['payment_type'], name='crm_order_payment_0afeaf_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['currency'], name='crm_order_currenc_6b9068_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status'], name='crm_order_status_51dd80_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['payment_id'], name='crm_order_payment_699f3d_idx'),
        ),
        migrations.AlterField(
            model_name='application',
            name='campaign',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.Campaign'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='wave_channel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='channel_campaigns', to='srbc.Wave'),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='wave_chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chat_campaigns', to='srbc.Wave'),
        ),
        migrations.AlterField(
            model_name='discountcode',
            name='applied_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='order',
            name='discount_code',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm.DiscountCode'),
        ),
        migrations.AlterField(
            model_name='order',
            name='tariff',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='srbc.Tariff'),
        ),
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='order',
            name='wave',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='wave_to_join', to='srbc.Wave', verbose_name='Payment wave'),
        ),
        migrations.AlterField(
            model_name='renewalrequest',
            name='usernote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='srbc.UserNote'),
        ),
        migrations.AlterField(
            model_name='admissiontestquestion',
            name='answer_carb',
            field=models.BooleanField(blank=True, default=False, verbose_name='Неверное количество углеводов'),
        ),
        migrations.AlterField(
            model_name='admissiontestquestion',
            name='answer_fat',
            field=models.BooleanField(blank=True, default=False, verbose_name='Превышение жирности'),
        ),
        migrations.AlterField(
            model_name='admissiontestquestion',
            name='answer_interval',
            field=models.BooleanField(blank=True, default=False, verbose_name='Нарушены интервалы'),
        ),
        migrations.AlterField(
            model_name='admissiontestquestion',
            name='answer_ok',
            field=models.BooleanField(blank=True, default=False, verbose_name='Соответствует методичке'),
        ),
        migrations.AlterField(
            model_name='admissiontestquestion',
            name='answer_protein',
            field=models.BooleanField(blank=True, default=False, verbose_name='Недостаток белка'),
        ),
        migrations.AlterField(
            model_name='admissiontestquestion',
            name='answer_sweet',
            field=models.BooleanField(blank=True, default=False, verbose_name='Сладкое натощак'),
        ),
        migrations.AlterField(
            model_name='admissiontestquestion',
            name='answer_weight',
            field=models.BooleanField(blank=True, default=False, verbose_name='Неверные навески'),
        ),
        migrations.AlterField(
            model_name='admissiontestquestion',
            name='is_active',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='application',
            name='admission_status',
            field=models.CharField(blank=True, choices=[('NOT_STARTED', 'Не дошел'), ('IN_PROGRESS', 'В процессе'), ('DONE', 'Завершил'), ('PASSED', 'Проверено, всё ок'), ('FAILED', 'Проверено, завалил'), ('REJECTED', 'Отказано'), ('ACCEPTED', 'Принят')], default='NOT_STARTED', max_length=100),
        ),
        migrations.AlterField(
            model_name='application',
            name='baby_case',
            field=models.CharField(choices=[('PREGNANT', 'Беременность'), ('FEEDING', 'Кормление грудью'), ('NONE', 'Ничего из перечисленного')], default='NONE', max_length=100, verbose_name='Особый случай'),
        ),
        migrations.AlterField(
            model_name='application',
            name='email_status',
            field=models.CharField(blank=True, choices=[('NEW', 'Новый'), ('PENDING', 'Ожидает подтверждения'), ('APPROVED', 'Подтвержден'), ('DISCONNECTED', 'Отписан')], default='NEW', max_length=25),
        ),
        migrations.AlterField(
            model_name='application',
            name='gender',
            field=models.CharField(choices=[('M', 'Мужской'), ('F', 'Женский')], default='F', max_length=1, verbose_name='Пол'),
        ),
        migrations.AlterField(
            model_name='application',
            name='is_approved',
            field=models.BooleanField(blank=True, default=False, verbose_name='Анкета проверена'),
        ),
        migrations.AlterField(
            model_name='application',
            name='is_payment_allowed',
            field=models.BooleanField(blank=True, default=False, verbose_name='Разрешена оплата'),
        ),
        migrations.AlterField(
            model_name='application',
            name='is_payment_special',
            field=models.BooleanField(blank=True, default=False, verbose_name='Особые условия оплаты'),
        ),
        migrations.AlterField(
            model_name='application',
            name='need_tracker',
            field=models.BooleanField(blank=True, default=False, verbose_name='Хочу фитнесс-трекер'),
        ),
        migrations.AlterField(
            model_name='application',
            name='social_acc_status',
            field=models.CharField(blank=True, choices=[('PENDING', 'Ожидает подтверждения'), ('APPROVED', 'Подтвержден'), ('SUSPICIOUS', 'Подозрительный'), ('REJECTED', 'Отклонён')], default='PENDING', max_length=25),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='is_active',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='discountcode',
            name='is_applied',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='discountcode',
            name='payment_type',
            field=models.CharField(blank=True, choices=[('CLUB', 'Оплата участия в клубе'), ('CHANNEL', 'Оплата участия в проекте (заочный)'), ('CHAT', 'Оплата участия в проекте (очный)')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='currency',
            field=models.CharField(choices=[('RUB', 'Рубли'), ('EUR', 'Евро')], default='RUB', max_length=3),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_provider',
            field=models.CharField(blank=True, choices=[('YA', 'Яндекс-Касса'), ('PP', 'PayPal'), ('MANUAL', 'Вручную')], default='YA', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_type',
            field=models.CharField(choices=[('CLUB', 'Оплата участия в клубе'), ('CHANNEL', 'Оплата участия в проекте (заочный)'), ('CHAT', 'Оплата участия в проекте (очный)')], max_length=100),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Ожидает оплаты'), ('PROCESSING', 'В обработке'), ('APPROVED', 'Оплачен'), ('CANCELED', 'Отменен')], default='PENDING', max_length=100),
        ),
        migrations.AlterField(
            model_name='renewalrequest',
            name='comment_internal',
            field=models.TextField(blank=True, default='', verbose_name='Служебная заметка'),
        ),
        migrations.AlterField(
            model_name='renewalrequest',
            name='payment_special',
            field=models.BooleanField(blank=True, default=False, verbose_name='Особые условия оплаты'),
        ),
        migrations.AlterField(
            model_name='renewalrequest',
            name='request_type',
            field=models.CharField(choices=[('POSITIVE', '#япродолжаю'), ('NEGATIVE', '#яНЕпродолжаю')], max_length=10, verbose_name='Хэштег'),
        ),
        migrations.AlterField(
            model_name='renewalrequest',
            name='status',
            field=models.CharField(blank=True, choices=[('NEW', 'Новый'), ('PENDING', 'Ожидает ответа участника'), ('PREACCEPTED', 'Предварительно одобрен'), ('TBD', 'Требуется согласование'), ('REJECTED', 'Отклонен'), ('ACCEPTED', 'Одобрен')], default='NEW', max_length=25),
        ),
        migrations.AlterField(
            model_name='telegrammailtemplate',
            name='text',
            field=markdownx.models.MarkdownxField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='useradmissiontest',
            name='status',
            field=models.CharField(blank=True, choices=[('NOT_STARTED', 'Не дошел'), ('IN_PROGRESS', 'В процессе'), ('DONE', 'Завершил'), ('PASSED', 'Проверено, всё ок'), ('FAILED', 'Проверено, завалил'), ('REJECTED', 'Отказано'), ('ACCEPTED', 'Принят')], default='NOT_STARTED', max_length=100),
        ),
        migrations.AlterField(
            model_name='useradmissiontestquestion',
            name='answer_carb',
            field=models.BooleanField(blank=True, default=False, verbose_name='Неверное количество углеводов'),
        ),
        migrations.AlterField(
            model_name='useradmissiontestquestion',
            name='answer_fat',
            field=models.BooleanField(blank=True, default=False, verbose_name='Превышение жирности'),
        ),
        migrations.AlterField(
            model_name='useradmissiontestquestion',
            name='answer_interval',
            field=models.BooleanField(blank=True, default=False, verbose_name='Нарушены интервалы'),
        ),
        migrations.AlterField(
            model_name='useradmissiontestquestion',
            name='answer_ok',
            field=models.BooleanField(blank=True, default=False, verbose_name='Соответствует методичке'),
        ),
        migrations.AlterField(
            model_name='useradmissiontestquestion',
            name='answer_protein',
            field=models.BooleanField(blank=True, default=False, verbose_name='Недостаток белка'),
        ),
        migrations.AlterField(
            model_name='useradmissiontestquestion',
            name='answer_sweet',
            field=models.BooleanField(blank=True, default=False, verbose_name='Сладкое натощак'),
        ),
        migrations.AlterField(
            model_name='useradmissiontestquestion',
            name='answer_weight',
            field=models.BooleanField(blank=True, default=False, verbose_name='Неверные навески'),
        ),
        migrations.AlterField(
            model_name='useradmissiontestquestion',
            name='is_answered',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
