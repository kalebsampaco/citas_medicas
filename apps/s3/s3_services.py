import re

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings


class S3ConfigError(Exception):
    """Raised when S3 credentials or mandatory settings are missing."""


def get_s3_client():
    access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
    if not access_key or not secret_key:
        raise S3ConfigError("AWS credentials are not configured (AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY).")
    return boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
        region_name='us-east-1',
        config=Config(signature_version='s3v4', retries={'max_attempts': 3})
    )

def get_company_bucket_name(rnc: str) -> str:
    """
    Devuelve el nombre de bucket para una empresa específica.
    Usa prefijo configurable `AWS_COMPANY_BUCKET_PREFIX` y el RNC.
    Si no hay prefijo definido, usa `<AWS_STORAGE_BUCKET_NAME>-company-<rnc>`.
    """
    rnc_sanitized = re.sub(r"[^0-9a-z-]", "", str(rnc).lower())
    prefix = getattr(settings, 'AWS_COMPANY_BUCKET_PREFIX', None)
    if prefix:
        return f"{prefix}{rnc_sanitized}"
    base = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'citas-bucket')
    return f"{base}-company-{rnc_sanitized}"

def ensure_bucket(bucket_name: str):
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = int(e.response.get('Error', {}).get('Code', 0))
        # 404 NoSuchBucket o 400 en MinIO
        if error_code in (404, 400):
            try:
                s3.create_bucket(Bucket=bucket_name)
                return True
            except ClientError:
                raise
        raise

def upload_file(file_obj, bucket, key):
    s3 = get_s3_client()
    try:
        ensure_bucket(bucket)
        s3.upload_fileobj(file_obj, bucket, key)
    except ClientError as e:
        # Intento de crear bucket y reintentar si fue por bucket inexistente
        if e.response.get('Error', {}).get('Code') in ('NoSuchBucket', '404'):
            ensure_bucket(bucket)
            s3.upload_fileobj(file_obj, bucket, key)
        else:
            raise

def generate_presigned_url(bucket, key, expires=3600):
    s3 = get_s3_client()
    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': key},
        ExpiresIn=expires
    )

def create_bucket(bucket_name):
    ensure_bucket(bucket_name)
