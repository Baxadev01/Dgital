# -*- coding: utf-8 -*-
import logging
from decimal import Decimal
from urllib.parse import urlparse

from django.db.models import Max
from django.utils import timezone
from rest_framework import serializers

from srbc.models import (ParticipationGoal, Profile, User, DiaryRecord, Wave, TechDutyShift, TechDuty, MealComponent,
                         DiaryMeal, InstagramImage, UserBookMark, SRBCImage, CheckpointPhotos, Checkpoint, MealFault,
                         DiaryMealFault, MealProduct, Tariff, TariffGroup, UserNote, UserReport)
from srbc.utils.drf import simplify_errors
from srbc.utils.personal_recommendation import get_recommendations

logger = logging.getLogger(__name__)


class SleepDurationField(serializers.DecimalField):
    MINUTES_ROUND = 15

    def round_to_minutes(self, value):
        correction = Decimal(0.5) if value >= 0 else Decimal(-0.5)
        return int(value / self.MINUTES_ROUND + correction) * self.MINUTES_ROUND

    def to_representation(self, value):
        minutes = value * 60
        return self.round_to_minutes(minutes)

    def to_internal_value(self, data):
        value = self.round_to_minutes(super(SleepDurationField, self).to_internal_value(data)) / Decimal(60)
        return self.quantize(self.validate_precision(value))


class TechDutyShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechDutyShift
        fields = ("id", "start_date", "end_date", "is_current")


class WaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wave
        fields = ("id", "title", "start_date", "is_in_club")


class UserNoteSerializer(serializers.ModelSerializer):

    author = serializers.SerializerMethodField()

    def get_author(self, obj):
        return obj.author.username

    class Meta:
        model = UserNote
        fields = ("id","has_meal_adjustments", "adjust_calories", "adjust_protein",
                  "add_fat", "adjust_fruits", "get_adjust_fruits_display",
                  "adjust_carb_bread_min", "adjust_carb_bread_late", "adjust_carb_carb_vegs",
                  "adjust_carb_sub_breakfast", "exclude_lactose", "restrict_lactose_casein", "date_added",
                  "author", "is_published", "content", "adjust_carb_mix_vegs",)
        read_only_fields=('id',)
        

class UserReportSerializer(serializers.ModelSerializer):

    is_processing = serializers.SerializerMethodField()

    def get_is_processing(self, obj):
        if obj.pdf_file:
            return False
        else:
            return True

    class Meta:
        model = UserReport
        fields = ('id', "pdf_file", 'date', 'is_processing')





class TariffGroupSerializer(serializers.ModelSerializer):
    """ Serializer to represent the Tariff model """

    meetings_access = serializers.SerializerMethodField()

    def get_meetings_access(self, obj):
        return obj.meetings_access != 'NONE'

    class Meta:
        model = TariffGroup

        fields = (
            'communication_mode',
            'expertise_access',
            'diary_access',
            'meetings_access',
            'kb_access',
        )
        read_only_fields = (
            'communication_mode',
            'expertise_access',
            'diary_access',
            'meetings_access',
            'kb_access',
        )


class TariffSerializer(serializers.ModelSerializer):
    """ Serializer to represent the Tariff model """

    tariff_group = TariffGroupSerializer()

    class Meta:
        model = Tariff

        fields = (
            'tariff_group',
        )
        read_only_fields = (
            'tariff_group',
        )


class ProfileSerializer(serializers.ModelSerializer):
    """ Serializer to represent the Participant model """
    wave = WaveSerializer()
    tariff = TariffSerializer()

    class Meta:
        model = Profile
        fields = (
            "user", "instagram", "wave", "is_pregnant", "warning_flag", "is_in_club", "is_perfect_weight",
            'is_active', 'valid_until', "is_meal_comments_allowed", "tariff",
        )

        read_only_fields = (
            "user", "instagram", "wave", "is_pregnant", "warning_flag", "is_in_club", "is_perfect_weight",
            'is_active', 'valid_until', "is_meal_comments_allowed", "tariff",
        )


class ProfileAdminSerializer(serializers.ModelSerializer):
    wave = WaveSerializer()

    class Meta:
        model = Profile
        fields = (
            "user", "instagram", "wave", "is_pregnant", "warning_flag", "is_in_club", "is_perfect_weight",
            'is_active', 'valid_until', "meal_analyze_mode", "is_meal_comments_allowed",
        )

        read_only_fields = (
            "user", "instagram", "wave", "is_pregnant", "warning_flag", "is_in_club", "is_perfect_weight",
            'is_active', 'valid_until', "meal_analyze_mode", "is_meal_comments_allowed",
        )


class DiaryRecordShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiaryRecord
        fields = (
            'date_text',
            'date_yesterday_text',
            'weight',
            'trueweight',
            'is_overcalory',
            'pers_rec_flag',
            'steps',
            'sleep',
            'sleep_text',
            'meals',
            'faults',
            'meal_short_formula',
            'has_sugar',
            'has_alco',
            'has_meals',
            'meal_status',
            'is_weight_accurate',
        )


class DiaryRecordSerializer(serializers.ModelSerializer):
    """ Serializer to representDiaryRecordSerializer the Diary Record model """

    class Meta:
        model = DiaryRecord
        fields = (
            "id",
            "user",
            "date",
            "weight",
            "trueweight",
            "steps",
            "sleep",
            "meals",
            "faults",
            "comment",
            "is_mono",
            "is_na_data",
            "is_na_meals",
            "is_fake_meals",
            "is_ooc",
            "is_unload",
            "is_overcalory",
            "pers_rec_flag",
            "has_meals",
            "is_meal_reviewed",
            "is_meal_validated",
            "has_meal_faults",
            "meal_status",
            "meal_self_review",
            "meal_short_formula",
            'is_weight_accurate',
        )
        read_only_fields = (
            "user",
            "date",
            "trueweight",
            "has_meals",
            "has_meal_faults",
            "is_meal_validated",
            "is_meal_reviewed",
            "is_fake_meals",
            "meal_status",
            "meal_self_review",
        )


class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ("id", "profile", "first_name", "last_name", "username")


class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "username")


class BookmarkToggleSerializer(serializers.ModelSerializer):
    action = serializers.ChoiceField(choices=['add', 'remove'], required=True)
    id = serializers.ModelField(model_field=UserBookMark()._meta.get_field('bookmarked_user'))

    class Meta:
        fields = ("id", "action",)
        model = UserBookMark


class TechDutySerializer(serializers.ModelSerializer):
    user = UserProfileSerializer()

    class Meta:
        model = TechDuty
        fields = ("mode", "user",)


class InstagramImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstagramImage
        fields = ("post_date", "post_url", "image", "post_text", "tags", "role")


class SRBCImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SRBCImage
        fields = ("id", "thumbnail", "image", "image_info", "date", "meta_data", "image_type",
                  "custom_image_is_editable")
        read_only_fields = ("thumbnail", "image", "meta_data", "image_type", "custom_image_is_editable")


class MealProductSerializer(serializers.ModelSerializer):
    id = serializers.ModelField(model_field=MealProduct()._meta.get_field('id'), required=False)

    class Meta:
        model = MealProduct
        fields = (
            "id",
            "title",
            "component_type",
            "comment",
        )


class MealComponentSerializer(serializers.ModelSerializer):
    id = serializers.ModelField(model_field=MealComponent()._meta.get_field('id'), required=False)
    meal_product = MealProductSerializer(required=False)

    def validate(self, data):
        if not data.get('meal_product_id') and not data.get('meal_product'):
            raise serializers.ValidationError("Функция добавление новых продуктов недоступна")

        # if not data.get('meal_product_id') and not data.get('meal_product'):
        #     data['component_type'] = 'new'
        #     other_title = data.get('other_title') or ''
        #     if not other_title.strip():
        #         raise serializers.ValidationError("Product title is required for new products")

        return data

    def validate_external_link(self, value):
        if not len(value):
            return None

        parsed_url = urlparse(value)

        # print(parsed_url)

        allowed_domains = (
            'www.fatsecret.ru',
            'mobile.fatsecret.ru',
            'www.calorizator.ru',
            'ru.wikipedia.org',
            'ru.m.wikipedia.org',
        )

        if not parsed_url.netloc:
            raise serializers.ValidationError('Некорректная ссылка на описание продукта')

        if not parsed_url.netloc.lower() in allowed_domains:
            raise serializers.ValidationError('Ссылка на описание продукта ведет на недопустимый сайт')

        return value

    class Meta:
        model = MealComponent
        fields = (
            "id", "component_type", "description", "weight", "is_sweet", "faults_data", "meal_product",
            "details_protein", "details_fat", "details_carb", "details_sugars",
            "other_title", "external_link",
        )
        read_only_fields = ("faults_data", "description", "component_type")


class MealFaultsSerializer(serializers.ModelSerializer):
    id = serializers.ModelField(model_field=MealFault()._meta.get_field('id'), required=False)

    class Meta:
        model = MealFault
        fields = ("id", "title", "scopes", "comment", )


class MealFaultsAdminSerializer(serializers.ModelSerializer):
    id = serializers.ModelField(model_field=MealFault()._meta.get_field('id'), required=False)

    class Meta:
        model = MealFault
        fields = ("id", "title", "scopes", "comment", "is_public", "is_manual", "code")
        read_only_fields = ("code",)


class FilteredListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(fault__is_public=True)
        return super(FilteredListSerializer, self).to_representation(data)


class DiaryMealFaultsSerializer(serializers.ModelSerializer):
    id = serializers.ModelField(model_field=DiaryMealFault()._meta.get_field('id'), required=False)
    fault = MealFaultsSerializer()
    meal_id = serializers.ModelField(model_field=DiaryMealFault()._meta.get_field('meal_id'), required=False,
                                     allow_null=True)
    meal_component_id = serializers.ModelField(model_field=DiaryMealFault()._meta.get_field('meal_component_id'),
                                               required=False, allow_null=True)

    class Meta:
        list_serializer_class = FilteredListSerializer
        model = DiaryMealFault
        fields = (
            "id",
            "fault",
            "meal_id",
            "meal_component_id",
            "comment",
        )


class DiaryMealFaultsAdminSerializer(serializers.ModelSerializer):
    id = serializers.ModelField(model_field=DiaryMealFault()._meta.get_field('id'), required=False)
    fault = MealFaultsAdminSerializer()
    meal_id = serializers.ModelField(model_field=DiaryMealFault()._meta.get_field('meal_id'), required=False,
                                     allow_null=True)
    meal_component_id = serializers.ModelField(model_field=DiaryMealFault()._meta.get_field('meal_component_id'),
                                               required=False, allow_null=True)

    class Meta:
        model = DiaryMealFault
        fields = (
            "id",
            "fault",
            "meal_id",
            "meal_component_id",
            "comment",
        )


class NewDiaryMealFaultsSerializer(serializers.ModelSerializer):
    fault = MealFaultsAdminSerializer()
    meal_id = serializers.ModelField(model_field=DiaryMealFault()._meta.get_field('meal_id'), required=False,
                                     allow_null=True)
    meal_component_id = serializers.ModelField(model_field=DiaryMealFault()._meta.get_field('meal_component_id'),
                                               required=False, allow_null=True)

    class Meta:
        model = DiaryMealFault
        fields = (
            "fault",
            "meal_id",
            "meal_component_id",
            "comment",
        )


class DiaryMealSerializer(serializers.ModelSerializer):
    components = MealComponentSerializer(many=True)
    id = serializers.ModelField(model_field=DiaryMeal()._meta.get_field('id'), required=False)
    meal_image_exif_datetime = serializers.CharField(source='image_exif_datetime', required=False)

    class Meta:
        model = DiaryMeal
        fields = (
            "id", "start_time", "start_time_is_next_day", "end_time", "end_time_is_next_day",
            "meal_type", "is_sweet", "components", "faults_data",
            "meal_image", "meal_image_status", "meal_image_exif_datetime",
            "hunger_intensity", "glucose_level", "glucose_unit"
            # "img_meta_data",
        )
        read_only_fields = (
            "faults_data", "meal_image_status", "meal_image_exif_datetime", "meal_image", "img_meta_data",)


class DiaryMealDataAdminSerializer(serializers.ModelSerializer):
    meals_data = DiaryMealSerializer(many=True, label='Данные рациона')
    user = UserProfileSerializer(required=False, label='Пользователь')
    meal_image = SRBCImageSerializer(required=False, label='Изображение рациона', read_only=True)
    faults_list = DiaryMealFaultsAdminSerializer(many=True, required=False)
    meal_reviewed_by = UserProfileSerializer(required=False)
    faulted_pers_reqs = serializers.SerializerMethodField()

    def get_faulted_pers_reqs(self, obj):
        return get_recommendations(obj.pers_req_faults)

    class Meta:
        model = DiaryRecord
        fields = (
            "wake_up_time",
            "bed_time",
            'bed_time_is_next_day',
            "water_consumed",
            "dairy_consumed",
            "meals_data",
            "meal_image",

            "user", "meal_hashtag",
            "is_meal_validated", "is_meal_reviewed",
            "faults_data", "is_fake_meals",
            "meal_validation_date",
            "meals", "faults", "is_overcalory", "pers_rec_flag",
            "is_ooc", "is_mono", "is_unload", 'anlz_mode',
            "faults_list", "meal_self_review", "meal_status", "meal_reviewed_by", "faulted_pers_reqs", "pers_req_faults",
            'is_weight_accurate',
        )
        read_only_fields = (
            "user", "is_meal_validated", "is_meal_reviewed", "meal_hashtag", "faults_data", "meals", "faults",
            "is_overcalory", "is_ooc", "pers_rec_flag",
            "is_mono", "is_unload", "is_fake_meals", "meal_image",
            "faults_list", "meal_self_review", "meal_reviewed_by"
        )


class DiarySerializer(serializers.ModelSerializer):
    meals_data = DiaryMealSerializer(many=True, label='Данные рациона')
    user = UserProfileSerializer(required=False, label='Пользователь')
    meal_image = SRBCImageSerializer(required=False, label='Изображение рациона', read_only=True)
    faults_list = DiaryMealFaultsSerializer(many=True, required=False)
    sleep = SleepDurationField(required=False, max_value=24 * 60, max_digits=5, min_value=0, decimal_places=2)

    @property
    def errors(self):
        # get errors
        errors = super(DiarySerializer, self).errors
        if not errors:
            return errors

        try:
            simplified_errors = simplify_errors(dict(errors), self.fields)
        except Exception as e:
            logger.exception(e)
            simplified_errors = []

        return {'errors': errors, 'simplified_errors': simplified_errors}

    class Meta:
        model = DiaryRecord
        fields = (
            "wake_up_time",
            "bed_time",
            'bed_time_is_next_day',
            "water_consumed",
            "dairy_consumed",
            "meals_data",
            "meal_image",

            "user", "meal_hashtag",

            "steps", "sleep", "weight", "trueweight",

            "is_meal_validated", "is_meal_reviewed",
            "faults_data", "is_fake_meals",
            "meal_validation_date",
            "meals", "faults", "is_overcalory", "pers_rec_flag",
            "is_ooc", "is_mono", "is_unload",
            "faults_list", "meal_self_review", "meal_status",
            "last_data_updated", "last_meal_updated",
            'is_weight_accurate',
        )


class DiaryTodaySerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(required=False, label='Пользователь')
    sleep = SleepDurationField(required=False, max_value=24 * 60, max_digits=5, min_value=0, decimal_places=2)

    class Meta:
        model = DiaryRecord
        fields = (
            "user",
            "sleep", "weight", "trueweight",
            "last_data_updated", 'last_sleep_updated',
            'last_weight_updated'
        )


class DiaryTomorrowSerializer(serializers.ModelSerializer):
    meals_data = DiaryMealSerializer(many=True, label='Данные рациона')
    meal_image = SRBCImageSerializer(required=False, label='Изображение рациона', read_only=True)
    faults_list = DiaryMealFaultsSerializer(many=True, required=False)

    class Meta:
        model = DiaryRecord
        fields = (
            "wake_up_time",
            "bed_time",
            'bed_time_is_next_day',
            "water_consumed",
            "meals_data",
            "meal_image",
            "steps",
            "is_meal_validated", "is_meal_reviewed",
            "faults_data", "is_fake_meals",
            "meal_validation_date", 'anlz_mode',
            "meals", "faults", "is_overcalory", "pers_rec_flag",
            "is_ooc", "is_mono", "is_unload",
            "faults_list", "meal_self_review", "meal_status",
            "last_steps_updated", "last_meal_updated",
            'is_weight_accurate',
        )


class DiaryMealDataSerializer(serializers.ModelSerializer):
    meals_data = DiaryMealSerializer(many=True, label='Данные рациона')
    user = UserProfileSerializer(required=False, label='Пользователь')
    meal_image = SRBCImageSerializer(required=False, label='Изображение рациона', read_only=True)
    faults_list = DiaryMealFaultsSerializer(many=True, required=False)
    faulted_pers_reqs = serializers.SerializerMethodField()

    def get_faulted_pers_reqs(self, obj):
        return get_recommendations(obj.pers_req_faults)

    @property
    def errors(self):
        # get errors
        errors = super(DiaryMealDataSerializer, self).errors
        if not errors:
            return errors

        try:
            simplified_errors = simplify_errors(dict(errors), self.fields)
        except Exception as e:
            logger.exception(e)
            simplified_errors = []

        return {'errors': errors, 'simplified_errors': simplified_errors}

    def validate(self, data):
        def get_error_text(start_text, wrong_meal):
            if wrong_meal['meal_type'] == DiaryMeal.MEAL_TYPE_SLEEP:
                text = "%s есть пересечение с дневным сном (%s - %s)" % (
                    start_text,
                    wrong_meal['start_time'].strftime('%H:%M'),
                    wrong_meal['end_time'].strftime('%H:%M')
                )
            else:
                text = "%s есть пересечение с приемом пищи (%s)" % (
                    start_text,
                    wrong_meal['start_time'].strftime('%H:%M')
                )
            return text

        # Время утреннего подъема позже, чем какой-нибудь элемент рациона (прием пищи либо дневной сон)
        wake_up_time = data.get('wake_up_time')
        if wake_up_time:
            wrong_meal = next((item for item in data['meals_data']
                               if item['start_time'] < wake_up_time and not item['start_time_is_next_day']), None)
            if wrong_meal:
                start_text = "Утренний подъем (%s):" % wake_up_time.strftime('%H:%M')
                raise serializers.ValidationError(get_error_text(start_text, wrong_meal))

        # Время ночного отбоя раньше, чем любой из элементов рациона
        sleep_time = data.get('bed_time')
        if sleep_time:
            if data.get('bed_time_is_next_day'):
                wrong_meal = next((item for item in data['meals_data']
                                   if (item['start_time'] > sleep_time
                                       and item['start_time_is_next_day'])
                                   or (item.get('end_time')
                                       and item.get('end_time_is_next_day')
                                       and item['end_time'] > sleep_time)), None)
            else:
                wrong_meal = next((item for item in data['meals_data']
                                   if (item['start_time'] > sleep_time
                                       or item['start_time_is_next_day'])
                                   or (item.get('end_time')
                                       and (
                                           item['end_time'] > sleep_time
                                           or item.get('end_time_is_next_day')
                                   )
                )), None)
            if wrong_meal:
                start_text = "Вечерний отбой (%s):" % sleep_time.strftime('%H:%M')
                raise serializers.ValidationError(get_error_text(start_text, wrong_meal))

        meals = data['meals_data']

        wrong_meal = None
        for i, meal in enumerate(meals):
            if meal['meal_type'] == DiaryMeal.MEAL_TYPE_SLEEP:

                if not meal.get('start_time', None):
                    raise serializers.ValidationError('Не задано время начала дневного сна')

                if not meal.get('end_time', None):
                    raise serializers.ValidationError('Не задано время завершения дневного сна')

                meal_start_is_next_day = meal.get('start_time_is_next_day', False)
                meal_end_is_next_day = meal.get('end_time_is_next_day', False)

                for j, item in enumerate(meals):
                    item_start_is_next_day = item.get('start_time_is_next_day', False)
                    item_end_is_next_day = item.get('end_time_is_next_day', False)

                    # между отбоем и подъемом дневного сна происходит отбой или подъем другого дневного сна
                    if item['meal_type'] == DiaryMeal.MEAL_TYPE_SLEEP:
                        # чтобы по второму кругу не сравнивать сон со сном
                        if j > i:
                            in_one_day = item_start_is_next_day == meal_end_is_next_day
                            not_left_cross = (in_one_day and meal['end_time'] <= item['start_time']) \
                                or (not in_one_day and item_start_is_next_day)

                            in_one_day = item_end_is_next_day == meal_start_is_next_day
                            not_right_cross = (in_one_day and meal['start_time'] >= item['end_time']) \
                                or (not in_one_day and meal_start_is_next_day)

                            if not_right_cross or not_left_cross:
                                continue
                            else:
                                wrong_meal = item
                                break
                    elif item['meal_type'] not in ['HUNGER', 'BLOOD_GLUCOSE']:
                        # между отбоем и подъемом дневного сна происходит прием пищи
                        start_in_one_day = item_start_is_next_day == meal_start_is_next_day
                        left_check = (start_in_one_day and meal['start_time'] >= item['start_time']) \
                            or (not start_in_one_day and meal_start_is_next_day)

                        end_in_one_day = item_start_is_next_day == meal_end_is_next_day
                        right_check = (end_in_one_day and meal['end_time'] <= item['start_time']) \
                            or (not end_in_one_day and item_start_is_next_day)

                        if left_check or right_check:
                            continue
                        else:
                            wrong_meal = item
                            break

                if wrong_meal:
                    start_text = "Дневной сон (%s - %s):" % (
                        meal['start_time'].strftime('%H:%M'),
                        meal['end_time'].strftime('%H:%M')
                    )
                    raise serializers.ValidationError(get_error_text(start_text, wrong_meal))

            elif meal['meal_type'] == DiaryMeal.MEAL_TYPE_HUNGER:
                hunger_intensity = meal.get('hunger_intensity', None)

                if not hunger_intensity:
                    raise serializers.ValidationError('Не задана интенсивность голода')

                elif hunger_intensity < 1 or hunger_intensity > 3:
                    raise serializers.ValidationError('Интенсивность голода должна быть целом числом от 1 до 3')

            elif meal['meal_type'] == DiaryMeal.MEAL_TYPE_BLOOD_GLUCOSE:
                if not meal.get('glucose_level', None):
                    raise serializers.ValidationError('Не задан результат замера глюкозы')

                if not meal.get('glucose_unit', None):
                    raise serializers.ValidationError('Не задана единица измерения замера глюкозы')

        return data

    def update(self, instance, validated_data):
        if not instance.id:
            instance.save()

        meals_data = validated_data.pop('meals_data')
        DiaryRecord.objects.filter(pk=instance.pk).update(**validated_data)
        meals_to_keep = []

        for meal_data in meals_data:
            meal_id = meal_data.pop("id", None)
            components_data = meal_data.pop('components')
            if meal_id:
                DiaryMeal.objects.filter(diary_id=instance.pk, pk=meal_id).update(**meal_data)
                meal = DiaryMeal.objects.filter(diary_id=instance.pk).get(pk=meal_id)
            else:
                meal = DiaryMeal.objects.create(diary=instance, **meal_data)

            meals_to_keep.append(meal.pk)

            components_to_keep = []
            for component_data in components_data:
                component_id = component_data.pop("id", None)

                component_data['meal_product_id'] = component_data.pop("meal_product", {}).pop('id', None)

                if component_data.get('meal_product_id'):
                    product = MealProduct.objects.get(pk=component_data['meal_product_id'])

                    if not product.is_verified:
                        continue

                    if not product.component_type:
                        continue
                else:
                    product = MealProduct(
                        component_type='new',
                        title=component_data.get("other_title").lower()
                    )

                if product.component_type not in ['unknown', 'new']:
                    component_data.pop("details_sugars", None)
                    component_data.pop("details_protein", None)
                    component_data.pop("details_fat", None)
                    component_data.pop("details_carb", None)

                component_data['details_sugars'] = component_data.get("details_sugars", False)

                if product.component_type != 'new':
                    component_data.pop("other_title", None)

                component_data['description'] = product.title

                if product.component_type in ['unknown', 'new']:
                    nutrition_unknown = component_data.get('details_protein') is None \
                        or component_data.get('details_fat') is None \
                        or component_data.get('details_carb') is None
                    if nutrition_unknown:
                        component_data['description'] = '%s (БЖУ неизвестны)' % component_data['description']
                    else:
                        has_sugars = component_data.get('details_sugars', False)
                        component_data['description'] = '%s (%.1f/%.1f/%.1f%s)' % (
                            component_data['description'],
                            component_data.get('details_protein', 0),
                            component_data.get('details_fat', 0),
                            component_data.get('details_carb', 0),
                            ', сахара' if has_sugars else '',
                        )

                component_data['component_type'] = product.component_type

                if component_id:
                    MealComponent.objects.filter(meal_id=meal.pk, pk=component_id).update(**component_data)
                    component = MealComponent.objects.filter(meal_id=meal.pk).get(pk=component_id)
                else:
                    component = MealComponent.objects.create(meal=meal, **component_data)

                components_to_keep.append(component.pk)
            MealComponent.objects.filter(meal_id=meal.pk).exclude(pk__in=components_to_keep).delete()
        DiaryMeal.objects.filter(diary_id=instance.pk).exclude(pk__in=meals_to_keep).delete()

        diary = DiaryRecord.objects.get(pk=instance.pk)

        return diary

    class Meta:
        model = DiaryRecord
        fields = (
            "wake_up_time",
            "bed_time",
            'bed_time_is_next_day',
            "water_consumed",
            "dairy_consumed",
            "meals_data",
            "meal_image",

            "user", "meal_hashtag",
            "is_meal_validated", "is_meal_reviewed",
            "faults_data", "is_fake_meals",
            "meal_validation_date",
            "meals", "faults", "is_overcalory", "pers_rec_flag",
            "is_ooc", "is_mono", "is_unload", "anlz_mode",
            "faults_list", "meal_self_review", "meal_status", "last_meal_updated", "faulted_pers_reqs",
            'is_weight_accurate',
        )
        read_only_fields = (
            "user", "is_meal_validated", "is_meal_reviewed", "meal_hashtag", "faults_data", "meals", "faults",
            "is_overcalory", "is_ooc", "pers_rec_flag",
            "is_mono", "is_unload", "is_fake_meals", "meal_image",
            "faults_list", "meal_self_review", "last_meal_updated",
        )


class MealComponentReviewSerializer(serializers.ModelSerializer):
    id = serializers.ModelField(model_field=MealComponent()._meta.get_field('id'), required=False)

    class Meta:
        model = MealComponent
        fields = ("id", "faults_data",)


class DiaryMealReviewSerializer(serializers.ModelSerializer):
    components = MealComponentReviewSerializer(many=True)
    id = serializers.ModelField(model_field=DiaryMeal()._meta.get_field('id'), required=False)

    class Meta:
        model = DiaryMeal
        fields = ("id", "components", "faults_data",)


class ParticipantDiaryReviewSerializer(serializers.ModelSerializer):
    faults_list = DiaryMealFaultsSerializer(many=True)

    def update(self, instance, validated_data):
        faults_list = validated_data.pop('faults_list', [])
        DiaryRecord.objects.filter(pk=instance.pk).update(**validated_data)
        existing_faults = DiaryMealFault.objects.filter(diary_record_id=instance.pk)
        fault_ids_to_delete = [f.id for f in existing_faults]
        for fault in faults_list:
            fault_id = fault.pop('id', None)
            meal_id = fault.pop('meal_id', None)
            component_id = fault.pop('meal_component_id', None)
            comment = fault.pop('comment', '')
            type_id = fault.pop('fault', {}).pop('id', None)

            if not type_id:
                raise serializers.ValidationError("Не указан тип жиронакопительного действия")

            if fault_id:
                fault_obj = DiaryMealFault.objects.filter(diary_record_id=instance.pk).get(pk=fault_id)
                fault_ids_to_delete.remove(fault_id)
            else:
                fault_obj = DiaryMealFault(diary_record_id=instance.pk)

            if meal_id:
                meal = DiaryMeal.objects.filter(diary=instance).get(id=meal_id)
                fault_obj.meal = meal

            fault_obj.meal_id = meal_id
            if component_id:
                meal_component = MealComponent.objects.filter(meal__diary=instance).get(id=component_id)
                fault_obj.meal_component = meal_component

            fault_obj.comment = comment

            fault = MealFault.objects.get(id=type_id)
            fault_obj.fault = fault

            fault_obj.save()

        DiaryMealFault.objects.filter(diary_record=instance, pk__in=fault_ids_to_delete).delete()

        faults_count = DiaryMealFault.objects.filter(diary_record=instance, fault__is_public=True).count()

        DiaryRecord.objects.filter(pk=instance.pk).update(faults=faults_count)
        diary = DiaryRecord.objects.get(pk=instance.pk)

        return diary

    class Meta:
        model = DiaryRecord
        fields = (
            "meals", "is_overcalory", "is_ooc", "is_mono", "pers_rec_flag",
            "is_unload", "faults_list"
        )


class DiaryReviewSerializer(serializers.ModelSerializer):
    meals_data = DiaryMealReviewSerializer(many=True)
    faults_list = DiaryMealFaultsAdminSerializer(many=True)

    def update(self, instance, validated_data):
        meals_data = validated_data.pop('meals_data')
        faults_list = validated_data.pop('faults_list', [])

        has_faults = False
        if len(validated_data.get('faults_data', [])):
            has_faults = True
        DiaryRecord.objects.filter(pk=instance.pk).update(**validated_data)
        for meal_data in meals_data:
            meal_id = meal_data.pop("id", None)
            components_data = meal_data.pop('components')

            if meal_id:
                DiaryMeal.objects.filter(diary_id=instance.pk, pk=meal_id).update(**meal_data)
                meal = DiaryMeal.objects.filter(diary_id=instance.pk).get(pk=meal_id)
                if len(meal.faults_data):
                    has_faults = True
            else:
                continue

            for component_data in components_data:
                component_id = component_data.pop("id", None)
                if component_id:
                    MealComponent.objects.filter(meal_id=meal.pk, pk=component_id).update(**component_data)
                    if len(component_data.get('faults_data', [])):
                        has_faults = True

        existing_faults = DiaryMealFault.objects.filter(diary_record_id=instance.pk)
        fault_ids_to_delete = [f.id for f in existing_faults]

        for fault in faults_list:
            fault_id = fault.pop('id', None)
            meal_id = fault.pop('meal_id', None)
            component_id = fault.pop('meal_component_id', None)
            comment = fault.pop('comment', '')
            type_id = fault.pop('fault', {}).pop('id', None)

            if not type_id:
                raise serializers.ValidationError("Не указан тип жиронакопительного действия")

            if fault_id:
                fault_obj = DiaryMealFault.objects.filter(diary_record_id=instance.pk).get(pk=fault_id)
                fault_ids_to_delete.remove(fault_id)
            else:
                fault_obj = DiaryMealFault(diary_record_id=instance.pk)

            if meal_id:
                meal = DiaryMeal.objects.filter(diary=instance).get(id=meal_id)
                fault_obj.meal = meal

            fault_obj.meal_id = meal_id
            if component_id:
                meal_component = MealComponent.objects.filter(meal__diary=instance).get(id=component_id)
                fault_obj.meal_component = meal_component

            fault_obj.comment = comment

            fault = MealFault.objects.get(id=type_id)
            fault_obj.fault = fault

            fault_obj.save()

        DiaryMealFault.objects.filter(diary_record=instance, pk__in=fault_ids_to_delete).delete()

        faults_count = DiaryMealFault.objects.filter(diary_record=instance, fault__is_public=True).count()

        DiaryRecord.objects.filter(pk=instance.pk).update(has_meal_faults=has_faults, faults=faults_count)
        diary = DiaryRecord.objects.get(pk=instance.pk)

        return diary

    class Meta:
        model = DiaryRecord
        fields = (
            "meals_data", "faults_data", "meals", "faults", "is_overcalory", "pers_rec_flag", "meal_hashtag",
            "is_ooc", "is_mono", "is_unload",
            "is_fake_meals",
            "faults_list",
            "pers_req_faults", "pers_rec_check_mode"
        )
        read_only_fields = ("meal_hashtag", "is_fake_meals", "faults_list", "faults")


class ParticipationGoalSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context.get('user')
        assert user is not None
        max_order_num = ParticipationGoal.objects.filter(user_id=user.id).aggregate(last_num=Max('order_num'))
        max_order_num = max_order_num['last_num'] or 0

        goal = ParticipationGoal(
            user=user,
            status=ParticipationGoal.STATUS_PROGRESS,
            title=validated_data.get('title'),
            text=validated_data.get('text'),
            status_changed_at=timezone.now(),
            order_num=max_order_num + 1
        )
        goal.save()

        return goal

    class Meta:
        model = ParticipationGoal
        fields = ('id', 'title', 'text', 'status', 'created_at', 'status_changed_at',)
        read_only_fields = ('id', 'created_at', 'status_changed_at',)


class ParticipationGoalOrderSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.order_num = validated_data.get('order_num')
        instance.save()
        return instance

    class Meta:
        model = ParticipationGoal
        fields = ('id', 'order_num',)
        read_only_fields = ('id',)


class ParticipationGoalStatusSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        if instance.status == validated_data.get('status'):
            return instance

        instance.status = validated_data.get('status')
        instance.status_changed_at = timezone.now()
        instance.save()

        return instance

    class Meta:
        model = ParticipationGoal
        fields = ('id', 'status', 'status_changed_at',)
        read_only_fields = ('id', 'status_changed_at',)

class CheckpointPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckpointPhotos
        fields = (
            'id', 'date',
            'front_image', 'side_image', 'rear_image',
            # 'cropped_front_image', 'cropped_side_image', 'cropped_rear_image',
            'crop_meta', 'status'
        )



