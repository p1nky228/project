"""
S3-совместимый клиент (SeaweedFS, MinIO, AWS S3) для загрузки фото ТО.

Использует boto3 для универсальной работы с любым S3-совместимым хранилищем.
"""

import logging
from io import BytesIO
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Client:
    """
    Клиент для работы с S3-совместимым хранилищем (SeaweedFS, MinIO, AWS S3).

    Использует настройки из config.settings:
    - S3_ENDPOINT_URL
    - S3_ACCESS_KEY
    - S3_SECRET_KEY
    - S3_BUCKET_NAME
    - S3_REGION
    """

    def __init__(self):
        self._client: Optional[boto3.client] = None
        self._bucket_name = settings.S3_BUCKET_NAME

    @property
    def client(self):
        """Ленивая инициализация boto3 клиента."""
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
            )

            # Создаем бакет, если не существует
            self._ensure_bucket_exists()

        return self._client

    def _ensure_bucket_exists(self) -> None:
        """Создает бакет, если он не существует."""
        try:
            self.client.head_bucket(Bucket=self._bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                try:
                    self.client.create_bucket(
                        Bucket=self._bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": settings.S3_REGION}
                    )
                    logger.info(f"Created bucket: {self._bucket_name}")
                except ClientError as create_error:
                    # Для us-east-1 LocationConstraint не нужен
                    if create_error.response["Error"]["Code"] == "InvalidLocationConstraint":
                        self.client.create_bucket(Bucket=self._bucket_name)
                        logger.info(f"Created bucket: {self._bucket_name}")
                    else:
                        logger.error(f"Failed to create bucket: {create_error}")
                        raise
            else:
                logger.error(f"Failed to check bucket exists: {e}")
                raise

    async def upload_file(
        self,
        file_bytes: bytes,
        object_name: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Загружает файл в S3-совместимое хранилище.

        Args:
            file_bytes: Байты файла
            object_name: Имя объекта в бакете (путь)
            content_type: MIME тип контента

        Returns:
            object_name (путь в S3)

        Raises:
            ClientError: При ошибке загрузки
        """
        try:
            data = BytesIO(file_bytes)
            data.seek(0)

            self.client.put_object(
                Bucket=self._bucket_name,
                Key=object_name,
                Body=data,
                ContentType=content_type,
            )

            logger.info(f"Uploaded file to S3: {object_name} ({len(file_bytes)} bytes)")
            return object_name

        except ClientError as e:
            logger.error(f"S3 upload error for {object_name}: {e}")
            raise

    async def delete_file(self, object_name: str) -> bool:
        """
        Удаляет файл из S3-совместимого хранилища.

        Args:
            object_name: Имя объекта в бакете

        Returns:
            True если файл был удален, False если не найден
        """
        try:
            self.client.delete_object(Bucket=self._bucket_name, Key=object_name)
            logger.info(f"Deleted file from S3: {object_name}")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                logger.warning(f"File not found in S3: {object_name}")
                return False
            logger.error(f"S3 delete error for {object_name}: {e}")
            raise

    def get_file_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Генерирует пресайнд URL для скачивания файла.

        Args:
            object_name: Имя объекта в бакете
            expires: Время жизни ссылки в секундах (по умолчанию 1 час)

        Returns:
            Пресайнд URL
        """
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket_name, "Key": object_name},
            ExpiresIn=expires,
        )

    def file_exists(self, object_name: str) -> bool:
        """
        Проверяет существование файла в S3.

        Args:
            object_name: Имя объекта в бакете

        Returns:
            True если файл существует
        """
        try:
            self.client.head_object(Bucket=self._bucket_name, Key=object_name)
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                return False
            raise


# Глобальный экземпляр клиента
_s3_client: Optional[S3Client] = None


def get_s3_client() -> S3Client:
    """Возвращает глобальный экземпляр S3 клиента (singleton)."""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client