import logging
import boto3
from botocore.exceptions import ClientError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class StorageService:
    """Service voor bestandsopslag via S3/MinIO."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
        )
        self.bucket = settings.S3_BUCKET
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Maak bucket aan als deze niet bestaat."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                logger.info(f"Bucket '{self.bucket}' aangemaakt")
            except ClientError as e:
                logger.error(f"Kan bucket niet aanmaken: {e}")

    async def upload_file(self, content: bytes, filename: str) -> str:
        """Upload een bestand naar S3/MinIO."""
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=filename,
                Body=content,
            )
            return f"{settings.S3_ENDPOINT}/{self.bucket}/{filename}"
        except ClientError as e:
            logger.error(f"Upload fout: {e}")
            raise

    async def get_file_url(self, filename: str) -> str:
        """Genereer een pre-signed URL voor een bestand."""
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": filename},
                ExpiresIn=3600,
            )
            return url
        except ClientError as e:
            logger.error(f"URL generatie fout: {e}")
            raise

    async def delete_file(self, filename: str) -> None:
        """Verwijder een bestand uit S3/MinIO."""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=filename)
        except ClientError as e:
            logger.error(f"Verwijder fout: {e}")
            raise

    async def get_file(self, filename: str) -> bytes:
        """Download een bestand van S3/MinIO."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=filename)
            return response["Body"].read()
        except ClientError as e:
            logger.error(f"Download fout: {e}")
            raise
