"""
MinIO (S3-совместимое хранилище) клиент для загрузки фото ТО.
"""

import logging
from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """
    Клиент для работы с MinIO/S3 хранилищем.

    Использует настройки из config.settings:
    - S3_ENDPOINT_URL
    - S3_ACCESS_KEY
    - S3_SECRET_KEY
    - S3_BUCKET_NAME
    - S3_REGION
    """

    def __init__(self):
        self._client: Optional[Minio] = None
        self._bucket_name = settings.S3_BUCKET_NAME

    @property
    def client(self) -> Minio:
        """Ленивая инициализация клиента MinIO."""
        if self._client is None:
            # Парсим endpoint URL
            endpoint = settings.S3_ENDPOINT_URL
            if endpoint.startswith("http://"):
                endpoint = endpoint[7:]
            elif endpoint.startswith("https://"):
                endpoint = endpoint[8:]

            self._client = Minio(
                endpoint=endpoint,
                access_key=settings.S3_ACCESS_KEY,
                secret_key=settings.S3_SECRET_KEY,
                secure=settings.S3_ENDPOINT_URL.startswith("https"),
                region=settings.S3_REGION,
            )

            # Создаем бакет, если не существует
            self._ensure_bucket_exists()

        return self._client

    def _ensure_bucket_exists(self) -> None:
        """Создает бакет, если он не существует."""
        try:
            if not self._client.bucket_exists(self._bucket_name):
                self._client.make_bucket(self._bucket_name)
                logger.info(f"Created bucket: {self._bucket_name}")

                # Устанавливаем политику публичного доступа для чтения (опционально)
                # policy = {
                #     "Version": "2012-10-17",
                #     "Statement": [
                #         {
                #             "Effect": "Allow",
                #             "Principal": {"AWS": "*"},
                #             "Action": ["s3:GetObject"],
                #             "Resource": [f"arn:aws:s3:::{self._bucket_name}/*"]
                #         }
                #     ]
                # }
                # self._client.set_bucket_policy(self._bucket_name, json.dumps(policy))
        except S3Error as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise

    async def upload_file(
        self,
        file_bytes: bytes,
        object_name: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Загружает файл в MinIO.

        Args:
            file_bytes: Байты файла
            object_name: Имя объекта в бакете (путь)
            content_type: MIME тип контента

        Returns:
            object_name (путь в MinIO)

        Raises:
            S3Error: При ошибке загрузки
        """
        try:
            # Загружаем через put_object
            data = BytesIO(file_bytes)
            data.seek(0)

            self.client.put_object(
                bucket_name=self._bucket_name,
                object_name=object_name,
                data=data,
                length=len(file_bytes),
                content_type=content_type,
            )

            logger.info(f"Uploaded file to MinIO: {object_name} ({len(file_bytes)} bytes)")
            return object_name

        except S3Error as e:
            logger.error(f"MinIO upload error for {object_name}: {e}")
            raise

    async def delete_file(self, object_name: str) -> bool:
        """
        Удаляет файл из MinIO.

        Args:
            object_name: Имя объекта в бакете

        Returns:
            True если файл был удален, False если не найден
        """
        try:
            self.client.remove_object(self._bucket_name, object_name)
            logger.info(f"Deleted file from MinIO: {object_name}")
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.warning(f"File not found in MinIO: {object_name}")
                return False
            logger.error(f"MinIO delete error for {object_name}: {e}")
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
        from datetime import timedelta
        return self.client.presigned_get_object(
            bucket_name=self._bucket_name,
            object_name=object_name,
            expires=timedelta(seconds=expires),
        )

    def file_exists(self, object_name: str) -> bool:
        """
        Проверяет существование файла в MinIO.

        Args:
            object_name: Имя объекта в бакете

        Returns:
            True если файл существует
        """
        try:
            self.client.stat_object(self._bucket_name, object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise


# Глобальный экземпляр клиента
_minio_client: Optional[MinIOClient] = None


def get_minio_client() -> MinIOClient:
    """Возвращает глобальный экземпляр MinIO клиента (singleton)."""
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client