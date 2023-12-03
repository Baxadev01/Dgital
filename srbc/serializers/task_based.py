from django.utils import timezone
from rest_framework import serializers

from srbc.models import Profile, User, DiaryRecord, Checkpoint
from srbc.tasks import update_collages_image_info, create_or_update_data_image, update_diary_trueweight

from srbc.serializers.general import DiarySerializer


class CheckpointMeasurementSerializer(serializers.ModelSerializer):
    MEASUREMENTS_FIELDS = ['measurement_point_01', 'measurement_point_02', 'measurement_point_03',
                           'measurement_point_04', 'measurement_point_05', 'measurement_point_06',
                           'measurement_point_07', 'measurement_point_08', 'measurement_point_09',
                           'measurement_point_10', 'measurement_point_11', 'measurement_point_12',
                           'measurement_point_13', 'measurement_point_14', 'measurement_point_15',
                           'measurement_point_16', 'measurement_height']

    def __init__(self, *args, **kwargs):
        super(CheckpointMeasurementSerializer, self).__init__(*args, **kwargs)

        # если is_measurements_done = True , все measurement-поля становятся not_null (нельзя удалить);
        if self.instance:
            if self.instance.is_measurements_done:
                for field in self.MEASUREMENTS_FIELDS:
                    self.fields[field].allow_null = False

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)

        # если все размеры выставили, то выставляем is_measurements_done
        if instance.is_filled:
            instance.is_measurements_done = True

            # все замеры выставили - обновляем Рост в профиле
            # но обновляем только в том случае, если этот замер - последний на текущий момент
            if instance.id == Checkpoint.objects.filter(user_id=instance.user_id).values('id').latest('date')['id']:
                Profile.objects.filter(user_id=instance.user_id).update(height=instance.measurement_height / 10)

        elif not instance.is_editable:
            # пытаются закрыть чекпоинт (is_editable=False), но не все чекпоинты заполнены
            raise serializers.ValidationError("All measurements must be filled.")

        instance.last_update = timezone.now()
        instance.save()

        if instance.is_editable is False:
            update_collages_image_info.delay(checkpoint_id=instance.pk)

        return instance

    class Meta:
        model = Checkpoint
        fields = ('id', 'date', 'is_editable', 'is_measurements_done', 'is_photo_done',
                  'measurement_point_01', 'measurement_point_02', 'measurement_point_03',
                  'measurement_point_04', 'measurement_point_05', 'measurement_point_06',
                  'measurement_point_07', 'measurement_point_08', 'measurement_point_09',
                  'measurement_point_10', 'measurement_point_11', 'measurement_point_12',
                  'measurement_point_13', 'measurement_point_14', 'measurement_point_15',
                  'measurement_point_16', 'measurement_height')
        read_only_fields = ('id', 'is_measurements_done', 'is_photo_done')

class CheckpointMeasurementSwaggerSerializer(serializers.Serializer):
    checkpoint = CheckpointMeasurementSerializer()


class CheckpointMeasurementsSwaggerSerializer(serializers.Serializer):
    checkpoints = CheckpointMeasurementSerializer(many=True)


class DiaryDataSerializer(DiarySerializer):
    class Meta(DiarySerializer.Meta):
        fields = (
            "id",
            "date",
            "steps", "sleep", "weight", "last_data_updated",
        )

        read_only_fields = (
            "date", "id", "last_data_updated",
        )

        extra_kwargs = {
            'weight': {'required': False, 'allow_null': False},
            'sleep': {'required': False, 'allow_null': False},
            'steps': {'required': False, 'allow_null': False},
        }

    def update(self, instance, validated_data):
        is_dirty = False
        is_weight_dirty = False
        now = timezone.now()

        if instance.weight != validated_data.get('weight', instance.weight):
            is_weight_dirty = True
            is_dirty = True
            instance.weight = validated_data.get('weight', instance.weight)
            instance.last_weight_updated = now

        if instance.steps != validated_data.get('steps', instance.steps):
            is_dirty = True
            instance.steps = validated_data.get('steps', instance.steps)
            instance.last_steps_updated = now

        if instance.sleep != validated_data.get('sleep', instance.sleep):
            is_dirty = True
            instance.sleep = validated_data.get('sleep', instance.sleep)
            instance.last_sleep_updated = now

        if is_dirty:
            instance.last_data_updated = now
            instance.save()

        return instance, is_dirty, is_weight_dirty


class DiaryRecordDataSerializer(serializers.ModelSerializer):

    def update(self, instance, validated_data):
        old_weight = instance.weight
        if 'steps' in validated_data:
            instance.steps = validated_data['steps']
        if 'sleep' in validated_data:
            instance.sleep = validated_data['sleep']
        if 'weight' in validated_data:
            instance.weight = validated_data['weight']

        instance.save()

        if old_weight and old_weight != instance.weight:
            # instance.user.profile.update_diary_trueweight(start_from=instance.date)
            update_diary_trueweight.delay(user_id=instance.user.pk, start_from=instance.date)
            # вес изменился, поэтому обновим данные фото-ленты
            update_collages_image_info.delay(diary_record_id=instance.pk)

        return instance

    class Meta:
        model = DiaryRecord
        fields = (
            "weight",
            "sleep",
            "steps",
            "date",
            "user"
        )

        read_only_fields = ("user", "date")
        # make fields required and not null
        extra_kwargs = {'weight': {'required': False, 'allow_null': True},
                        'sleep': {'required': False, 'allow_null': True},
                        'steps': {'required': False, 'allow_null': True}}
