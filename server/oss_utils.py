import os
import uuid
import oss2
from config import (
    OSS_ENDPOINT,
    OSS_BUCKET_NAME,
    OSS_ACCESS_KEY_ID,
    OSS_ACCESS_KEY_SECRET
)

auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)


def upload_avatar_to_oss(file_storage):
    """
    上传头像到 OSS
    :param file_storage: Flask request.files['avatar']
    :return: object_key
    """
    original_name = file_storage.filename or "avatar.png"
    ext = os.path.splitext(original_name)[1] or ".png"
    object_key = f"users/{uuid.uuid4().hex}{ext}"

    bucket.put_object(object_key, file_storage.stream)
    return object_key