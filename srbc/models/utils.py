import os
from uuid import uuid4


def checkpoint_image_upload_to(instance, field, filename):
    return os.path.join(
        'checkpoints',
        '%s' % instance.user_id,
        instance.date.strftime('%Y-%m-%d'),
        "%s-%s%s" % (field, str(uuid4().hex), os.path.splitext(filename)[1])
    )
