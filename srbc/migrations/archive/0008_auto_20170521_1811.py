# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('srbc', '0007_auto_20170521_1759'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='checkpointrecord',
            name='front_image_id',
        ),
        migrations.RemoveField(
            model_name='checkpointrecord',
            name='measurements_image_id',
        ),
        migrations.RemoveField(
            model_name='checkpointrecord',
            name='rear_image_id',
        ),
        migrations.RemoveField(
            model_name='checkpointrecord',
            name='side_image_id',
        ),
        migrations.RemoveField(
            model_name='checkpointrecord',
            name='weight_image_id',
        ),
        migrations.RemoveField(
            model_name='diaryrecord',
            name='data_image_id',
        ),
        migrations.RemoveField(
            model_name='diaryrecord',
            name='meal_image_id',
        ),
        migrations.RemoveField(
            model_name='instagramimage',
            name='image_class',
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='front_image',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='CheckpointPhotoFront', blank=True, to='srbc.InstagramImage', null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='measurements_image',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='CheckpointDataMeasurements', blank=True, to='srbc.InstagramImage', null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='rear_image',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='CheckpointPhotoRear', blank=True, to='srbc.InstagramImage', null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='side_image',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='CheckpointPhotoSide', blank=True, to='srbc.InstagramImage', null=True),
        ),
        migrations.AddField(
            model_name='checkpointrecord',
            name='weight_image',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='CheckpointDataWeight', blank=True, to='srbc.InstagramImage', null=True),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='data_image',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='DiaryImageData', blank=True, to='srbc.InstagramImage', null=True),
        ),
        migrations.AddField(
            model_name='diaryrecord',
            name='meal_image',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='DiaryImageFood', blank=True, to='srbc.InstagramImage', null=True),
        ),
        migrations.AddField(
            model_name='instagramimage',
            name='post_url',
            field=models.CharField(default='', max_length=1024),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='instagramimage',
            name='role',
            field=models.CharField(default='UNKNOWN', max_length=100, choices=[(b'FOOD', 'Food'), (b'PHOTO', 'Photo'), (b'DATA', 'Data'), (b'MEASURE', 'Measurements'), (b'UNKNOWN', 'Unknown'), (b'GOAL', 'Goals')]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='instagramimage',
            name='post_text',
            field=models.TextField(null=True, blank=True),
        ),
    ]
