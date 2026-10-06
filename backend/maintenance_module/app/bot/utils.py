"""
Вспомогательные функции для бота ТО.
"""

import math
from typing import Optional
from uuid import UUID

from aiogram.types import PhotoSize
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.minio_client import MinIOClient


def validate_gps(
    user_lat: float,
    user_lon: float,
    apparatus_lat: float,
    apparatus_lon: float,
    max_distance: float = 200.0
) -> bool:
    """
    Проверяет, находится ли пользователь в радиусе max_distance метров от аппарата.

    Использует формулу гаверсинуса для расчета расстояния между двумя точками на сфере.

    Args:
        user_lat: Широта пользователя
        user_lon: Долгота пользователя
        apparatus_lat: Широта аппарата
        apparatus_lon: Долгота аппарата
        max_distance: Максимальное расстояние в метрах (по умолчанию 200м)

    Returns:
        True если расстояние <= max_distance, иначе False
    """
    # Радиус Земли в метрах
    R = 6371000.0

    # Переводим градусы в радианы
    lat1 = math.radians(user_lat)
    lon1 = math.radians(user_lon)
    lat2 = math.radians(apparatus_lat)
    lon2 = math.radians(apparatus_lon)

    # Разности координат
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Формула гаверсинуса
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    return distance <= max_distance


async def upload_photo_to_minio(
    photo: PhotoSize,
    task_id: UUID,
    step: int,
    minio_client: MinIOClient,
    bot,  # Bot instance required - avoids Bot.get_current() returning None
    max_retries: int = 3
) -> Optional[str]:
    """
    Загружает фото в MinIO с повторными попытками.

    Args:
        photo: Объект PhotoSize от Telegram (последний/наибольший размер)
        task_id: ID задания ТО
        step: Номер шага (1-7)
        minio_client: Клиент MinIO
        bot: Экземпляр Bot (обязательный, чтобы избежать None от Bot.get_current())
        max_retries: Максимальное количество попыток загрузки

    Returns:
        s3_key (путь в MinIO) или None при ошибке
    """
    if bot is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("Bot instance is None, cannot upload photo")
        return None

    # Формируем имя объекта: to_tasks/{task_id}/step_{step}_{file_id}.jpg
    file_name = f"to_tasks/{task_id}/step_{step}_{photo.file_id}.jpg"

    for attempt in range(max_retries):
        try:
            # Скачиваем файл из Telegram
            file = await bot.get_file(photo.file_id)
            file_bytes = await bot.download_file(file.file_path)
            file_bytes.seek(0)
            content = file_bytes.read()

            # Загружаем в MinIO
            s3_key = await minio_client.upload_file(
                file_bytes=content,
                object_name=file_name
            )

            return s3_key

        except Exception as e:
            if attempt == max_retries - 1:
                # Последняя попытка - логируем ошибку и возвращаем None
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to upload photo to MinIO after {max_retries} attempts: {e}",
                    extra={"task_id": str(task_id), "step": step}
                )
                return None

            # Ждем перед повторной попыткой (exponential backoff)
            import asyncio
            await asyncio.sleep(2 ** attempt)

    return None


async def download_photo_bytes(photo: PhotoSize, bot) -> Optional[bytes]:
    """
    Скачивает фото из Telegram и возвращает байты.

    Args:
        photo: Объект PhotoSize
        bot: Экземпляр Bot

    Returns:
        Байты изображения или None при ошибке
    """
    try:
        file = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file.file_path)
        file_bytes.seek(0)
        return file_bytes.read()
    except Exception:
        return None


def get_largest_photo(photos: list[PhotoSize]) -> PhotoSize:
    """
    Возвращает фото наибольшего размера из списка.

    Args:
        photos: Список объектов PhotoSize

    Returns:
        PhotoSize с максимальным размером (width * height)
    """
    return max(photos, key=lambda p: p.width * p.height)


def format_to_step_name(step: int) -> str:
    """
    Возвращает человекочитаемое название шага ТО.

    Args:
        step: Номер шага (1-7)

    Returns:
        Название шага на русском
    """
    step_names = {
        1: "Фото общего вида аппарата",
        2: "Фото узла розлива",
        3: "Фото фильтров с этикетками",
        4: "Показания счетчиков",
        5: "Сумма инкассации",
        6: "Фото изъятых денег",
        7: "Комментарий",
    }
    return step_names.get(step, f"Шаг {step}")


def validate_photo_size(file_size: int, max_size_mb: int = 10) -> bool:
    """
    Проверяет, не превышает ли размер фото максимально допустимый.

    Args:
        file_size: Размер файла в байтах
        max_size_mb: Максимальный размер в МБ

    Returns:
        True если размер допустим, иначе False
    """
    max_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_bytes


async def create_to_photos_from_state(
    session: AsyncSession,
    task_id: UUID,
    photos_data: dict[int, str]
) -> None:
    """
    Создает записи TOPhoto в БД из данных FSM.

    Args:
        session: Асинхронная сессия БД
        task_id: ID задания ТО
        photos_data: Словарь {step_number: s3_key}
    """
    from app.models.to_photo import TOPhoto

    for step_number, s3_key in photos_data.items():
        to_photo = TOPhoto(
            task_id=task_id,
            step_number=step_number,
            s3_key=s3_key,
            file_path=s3_key,  # file_path = s3_key для совместимости
        )
        session.add(to_photo)

    await session.flush()