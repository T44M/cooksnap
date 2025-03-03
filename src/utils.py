import os
import boto3
import requests
import logging
from io import BytesIO

# ロガー設定
logger = logging.getLogger()

def get_line_image(line_bot_api, message_id):
    """
    LINE APIから画像を取得する
    """
    try:
        message_content = line_bot_api.get_message_content(message_id)
        image_data = BytesIO()
        for chunk in message_content.iter_content():
            image_data.write(chunk)
        image_data.seek(0)
        return image_data
    except Exception as e:
        logger.error(f"Error getting image from LINE: {e}")
        raise

def upload_to_s3(image_data, user_id, bucket_name):
    """
    画像をS3にアップロードする
    """
    try:
        s3 = boto3.client('s3')
        file_path = f"images/{user_id}/{user_id}_{int(datetime.now().timestamp())}.jpg"
        
        s3.upload_fileobj(
            image_data,
            bucket_name,
            file_path,
            ExtraArgs={'ContentType': 'image/jpeg'}
        )
        
        # S3のURLを生成
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{file_path}"
        return s3_url
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
        raise