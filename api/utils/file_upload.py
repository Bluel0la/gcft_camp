import boto3, os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv(".env")

s3_client = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

MAX_PRESIGNED_EXPIRATION = 604_800  # 7 days
DEFAULT_EXPIRATION = min(
    int(os.getenv("PRESIGNED_URL_EXPIRATION", 600)), MAX_PRESIGNED_EXPIRATION
)


def create_download_presigned_url(
    object_key: str, expiration: int = DEFAULT_EXPIRATION
) -> str:
    expiration = min(expiration, MAX_PRESIGNED_EXPIRATION)

    try:
        return s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": object_key,
            },
            ExpiresIn=expiration,
        )
    except ClientError as e:
        raise RuntimeError(f"S3 download URL generation failed: {e}")


def upload_to_s3(file_bytes: bytes, object_key: str, content_type: str) -> str:
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
            Body=file_bytes,
            ContentType=content_type,
            CacheControl="public, max-age=604800",
        )
    except ClientError as e:
        raise RuntimeError(f"S3 upload failed: {e}")

    return create_download_presigned_url(object_key)


def delete_from_s3(object_key: str) -> None:
    s3_client.delete_object(
        Bucket=BUCKET_NAME,
        Key=object_key,
    )
