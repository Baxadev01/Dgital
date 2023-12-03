import os

from uuid import uuid4


def picture_upload_to(instance, filename):
    return os.path.join('pictures', str(instance.uid),
                        "image%s" % os.path.splitext(filename)[1])


def generate_uuid():
    return str(uuid4().hex)
