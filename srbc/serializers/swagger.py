from rest_framework import serializers
from srbc.serializers.general import NewDiaryMealFaultsSerializer, SRBCImageSerializer, DiaryMealDataSerializer, DiaryMealSerializer, MealComponentSerializer
from srbc.models import CheckpointPhotos, DiaryRecord, DiaryMeal, MealComponent
from content.serializers import AnalysisTemplateSerializer
from content.serializers import (
    TGMessageSerializer,
    TGPostSerializer
    )

class MealComponentProtein(serializers.Serializer):
    min_percent = serializers.FloatField(required=False)
    max_size = serializers.IntegerField(required=False)
    required = serializers.BooleanField(required=False)
    components = serializers.ListField(child=serializers.CharField(required=False), required=False)
    amount = serializers.IntegerField(required=False)

class MealComponentGlucose(serializers.Serializer):
    components = serializers.ListField(child=serializers.CharField(required=False), required=False)
    amount = serializers.IntegerField(required=False)

class MealComponentFat(serializers.Serializer):
    components = serializers.ListField(child=serializers.CharField(required=False), required=False)
    amount = serializers.IntegerField(required=False)

class MealComponentExtra(serializers.Serializer):
    components = serializers.ListField(child=serializers.CharField(required=False), required=False)

class MealComponents(serializers.Serializer):

    MEALS = serializers.ListField(child=serializers.TimeField(format="%H:%M", required=False), required=False)
    EXTRA = MealComponentExtra(required=False)
    FAT = MealComponentFat(required=False)
    FIBER = MealComponentProtein(required=False)
    GLUCOSE = MealComponentGlucose(required=False)
    PROTEIN = MealComponentProtein(required=False)
    STARCH = MealComponentGlucose(required=False)

class MealContainers(serializers.Serializer):

    BREAKFAST = MealComponents(required=False)
    BRUNCH = MealComponents(required=False)
    LUNCH = MealComponents(required=False)
    MERIENDA = MealComponents(required=False)
    DINNER = MealComponents(required=False)
    LATE = MealComponents(required=False)

class MealsMsgParamsNutration(serializers.Serializer):
    min = serializers.IntegerField(required=False)
    max = serializers.IntegerField(required=False)
    total = serializers.IntegerField(required=False)

class MealsMsgParamsShema(serializers.Serializer):
    component_type = serializers.CharField(required=False)
    weight = serializers.IntegerField(required=False)
    weight_min = serializers.IntegerField(required=False)
    weight_max = serializers.IntegerField(required=False)

class MealsMsgParams(serializers.Serializer):
    NUTRITION = MealsMsgParamsNutration(required=False)
    MEAL_SCHEMA = MealsMsgParamsShema(required=False)


class MealsMsgCodes(serializers.Serializer):

    code = serializers.ChoiceField(choices=[
        'MEAL_NUTRITION_SCHEMA_EXC',
        'MEAL_NUTRITION_SCHEMA_DEF',
        'MEALS_NUTRITION_ADJUST',
        'MEALS_NUTRITION_OK',
        'PR_ADJ_FRUITS_CARBVEG',
        'PR_ADJ_FRUITS_RSTR_SUGAR',
        'PR_ADJ_FRUITS_EXCL_SUGAR',
        'PR_ADJ_FRUITS_RSTR_FRUITS',
        'PR_ADJ_CARB_CARBVEGS_VEGS',
        'PR_ADJ_CARB_CARBVEGS_CARB',
        'PR_EXCLUDE_LACT',
        'PR_RESTRICT_LACT_CAS',
        'MEAL_NUTRITION_SCHEMA_MIS',
    ], required=False)
    params = MealsMsgParams(required=False)

class MealStatComponentExtra(serializers.Serializer):
    kcal = serializers.FloatField(required=False)
    components = serializers.ListField(child=serializers.CharField(required=False), required=False)
    quant_amount = serializers.IntegerField(required=False)

class MealStatComponentRegular(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        'NOT_NEED_NOT_ATE',
        'NOT_NEED_BUT_ATE',
        'NEED_BUT_NOT_ATE',
        'NEED_AND_ATE',
        'NEED_BUT_ATE_MORE',
        'NEED_BUT_ATE_LESS',
    ], required=False)

class MealStatComponents(serializers.Serializer):

    MEALS = serializers.ListField(child=serializers.TimeField(format="%H:%M", required=False), required=False)
    EXTRA = MealStatComponentExtra(required=False)
    FIBER = MealStatComponentRegular(required=False)
    PROTEIN = MealStatComponentRegular(required=False)
    STARCH = MealStatComponentRegular(required=False)

class MealStatContainers(serializers.Serializer):

    BREAKFAST = MealStatComponents(required=False)
    BRUNCH = MealStatComponents(required=False)
    LUNCH = MealStatComponents(required=False)
    MERIENDA = MealStatComponents(required=False)
    DINNER = MealStatComponents(required=False)
    LATE = MealStatComponents(required=False)


class MealDayStat(serializers.Serializer):
    FIBER = serializers.ChoiceField(choices=[
        'SUCCESS',
        'INSUFFICIENT',
        'EXCESS',
        'IMBALANCE',
    ])
    STARCH = serializers.ChoiceField(choices=[
        'SUCCESS',
        'INSUFFICIENT',
        'EXCESS',
        'IMBALANCE',
    ])
    PROTEIN = serializers.ChoiceField(choices=[
        'SUCCESS',
        'INSUFFICIENT',
        'EXCESS',
        'IMBALANCE',
    ])

class AnalysisTemplateSwagger(serializers.Serializer):
    templates = AnalysisTemplateSerializer(many=True, required=False)

class MealStatByDateSwagger(serializers.Serializer):
    containers = MealStatContainers(required=False)
    day_stat = MealDayStat(required=False)


class AnalysisAdminSerializer(serializers.Serializer):
    content = serializers.CharField()

    adjust_calories = serializers.IntegerField(label='Калорийность рациона', min_value=-100, max_value=100, required=False)
    adjust_protein = serializers.IntegerField(label='Белковость рациона', min_value=-100, max_value=100, required=False)
    add_fat = serializers.BooleanField(label='Добавить жиров', required=False)

    adjust_fruits = serializers.ChoiceField(label='Ограничение фруктов', initial='NO', required=False, choices=[
        'NO',
        'RESTRICT',
        'EXCLUDE',
    ])
    adjust_carb_mix_vegs = serializers.BooleanField(label='Смешивать овощи', required=False)
    adjust_carb_bread_min = serializers.BooleanField(label='Минимизировать хлеб', required=False)
    adjust_carb_bread_late = serializers.BooleanField(label='Убрать хлеб из ужина', required=False)
    adjust_carb_carb_vegs = serializers.BooleanField(label='Исключить запасающие овощи после обеда', required=False)
    adjust_carb_sub_breakfast = serializers.BooleanField(label='Замена длинных углеводов на овощи (завтрак по схеме обеда)',
                                                   required=False)
    exclude_lactose = serializers.BooleanField(label='Исключить молочные сахара', required=False)
    restrict_lactose_casein = serializers.BooleanField(
        label='Ограничить молочные сахара и казеин вторым завтраком', required=False
    )

    alarm = serializers.ChoiceField(label='Аларм', required=False,
                              choices=[
                                  'TEST',
                                    'OBSERVATION',
                                    'TREATMENT',
                                    'DANGER',
                                    'PR',
                                    'OOC',
                                    'OK',
                              ])
    
class MealProductDataSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    
class MealComponentDataSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(required=False)
    meal_product = MealProductDataSerializer(required=False)

    class Meta:
        model = MealComponent
        fields = (
            "id", "description", "weight", "is_sweet", "faults_data", "meal_product",
            "details_protein", "details_fat", "details_carb", "details_sugars",
            "other_title", "external_link",
        )
        extra_kwargs = {'weight': {'required': False}, 'description': {'required': False}}
        
class DiaryMealDataSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    components = MealComponentDataSerializer(many=True, required=False)

    class Meta:
        model = DiaryMeal
        fields = (
            "start_time",
            "start_time_is_next_day",
            "end_time",
            "end_time_is_next_day",
            "meal_type",
            "img_meta_data",
            "meal_image_status",
            "is_sweet",
            "is_filled",
            "is_overcalory",
            "scores",
            "faults_data",
            "hunger_intensity",
            "glucose_level",
            "glucose_unit",
            "id", 
            "components", 
        )
        extra_kwargs = {'meal_type': {'required': False}, 'start_time': {'required': False}}


class MealFaultsByDateSwagger(serializers.Serializer):
    
    status = 'OK'
    data = NewDiaryMealFaultsSerializer(many=True, required=False)
    rec_status = serializers.ChoiceField(choices=['OK', 'F'],required=False)
    rec_faults = serializers.ListField(child=serializers.CharField(required=False), required=False)
    containers = MealContainers(required=False)
    messages = MealsMsgCodes(required=False)
    report = serializers.ListField(child=serializers.CharField(required=False), required=False )
    is_reliable = serializers.BooleanField(required=False)


class CheckpointPhotoSwaggerSerializer(serializers.ModelSerializer):
    wave_checkpoints_exists = serializers.BooleanField()
    collages = SRBCImageSerializer()

    class Meta:
        model = CheckpointPhotos
        fields = (
            'id', 'date',
            'front_image', 'side_image', 'rear_image', 
            # 'cropped_front_image', 'cropped_side_image', 'cropped_rear_image',
            'crop_meta', 'status',
            'wave_checkpoints_exists', 'collages',
        )

class FaultSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    code = serializers.ChoiceField(choices=[
        'DATA_COMP_NUTRITION',
        'PHOTO_MEAL_EXTRACOMP',
        'PHOTO_COMP_MISSING',
        'PHOTO_COMP_DIFFERENT',
        ], required=True)

class FaultItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    meal_id = serializers.IntegerField(required=False)
    meal_component_id = serializers.IntegerField(required=False)
    comment = serializers.IntegerField(required=False)
    fault = FaultSerializer(required=True)

class PutMealsAdminSwaggerSerializer(serializers.ModelSerializer):
    
    faults_list = FaultItemSerializer(required=True)
    fake = serializers.BooleanField(required=False)
    per_req_faults = serializers.ListField(child=serializers.CharField(required=False), required=False)
    meals_data = DiaryMealDataSerializer(many=True, label='Данные рациона', required=False)

    class Meta:
        model = DiaryRecord
        fields = (
            'weight',
            'trueweight',
            'sleep',
            'steps',
            'meals',
            'is_pregnant',
            'is_perfect_weight',
            'is_sick',
            'is_meal_validated',
            'meal_validation_date',
            'is_overcalory',
            'is_mono',
            'is_unload',
            'is_ooc',
            'is_na_meals',
            'is_na_data',
            'comment',
            'wake_up_time',
            'bed_time',
            'bed_time_is_next_day',
            'water_consumed',
            'dairy_consumed',
            'meal_self_review',
            'last_data_updated',
            'last_meal_updated',
            'last_sleep_updated',
            'last_steps_updated',
            'last_weight_updated',
            'anlz_mode',
            'is_weight_accurate',
            'pers_rec_flag',
            'faults_list',
            'fake',
            'per_req_faults',
            'meals_data',

        )
        extra_kwargs = {'pers_rec_flag': {'required': True}}

class PutDiaryMealsSwaggerSerializer(serializers.ModelSerializer):
    verified = serializers.BooleanField(required=False)
    weight_accurate = serializers.BooleanField(required=False)
    fake = serializers.BooleanField(required=False)

    meals_data = DiaryMealDataSerializer(many=True, label='Данные рациона', required=False)

    class Meta:
        model = DiaryRecord
        fields = (
            
            'weight',
            'trueweight',
            'sleep',
            'steps',
            'meals',
            'is_pregnant',
            'is_perfect_weight',
            'is_sick',
            'is_meal_validated',
            'meal_validation_date',
            'is_overcalory',
            'is_mono',
            'is_unload',
            'is_ooc',
            'is_na_meals',
            'is_na_data',
            'comment',
            'wake_up_time',
            'bed_time',
            'bed_time_is_next_day',
            'water_consumed',
            'dairy_consumed',
            'meal_self_review',
            'last_data_updated',
            'last_meal_updated',
            'last_sleep_updated',
            'last_steps_updated',
            'last_weight_updated',
            'anlz_mode',
            'is_weight_accurate',
            'faults_data',

            "meals_data",
            "verified",
            "weight_accurate",
            "fake",
        )

class AddPostTelegramSwagger(serializers.Serializer):

    post = TGPostSerializer()
    messages = TGMessageSerializer(many=True)