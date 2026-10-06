"""
NotificationService для отправки уведомлений в Telegram.

Интегрируется с APScheduler задачами и ботом для отправки:
- Напоминаний о предстоящем ТО (за 2 дня, в день ТО)
- Уведомлений админам о просроченных ТО
- Уведомлений о результатах модерации ТО
"""

import logging
from typing import Optional
from uuid import UUID

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

from app.core.config import settings
from app.bot.keyboards import get_start_to_keyboard

logger = logging.getLogger(__name__)

# Глобальный экземпляр бота для отправки уведомлений
_notification_bot: Optional[Bot] = None


def get_notification_bot() -> Optional[Bot]:
    """Возвращает глобальный экземпляр бота для уведомлений."""
    global _notification_bot
    if _notification_bot is None and settings.BOT_TOKEN:
        _notification_bot = Bot(token=settings.BOT_TOKEN)
    return _notification_bot


async def close_notification_bot() -> None:
    """Закрывает сессию бота уведомлений."""
    global _notification_bot
    if _notification_bot:
        await _notification_bot.session.close()
        _notification_bot = None


async def send_to_technician(
    telegram_id: int,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> bool:
    """
    Отправляет сообщение технику.

    Args:
        telegram_id: Telegram ID техника
        text: Текст сообщения
        reply_markup: Опциональная клавиатура

    Returns:
        True если отправлено успешно, False при ошибке
    """
    bot = get_notification_bot()
    if not bot:
        logger.error("Notification bot not initialized (BOT_TOKEN not set)")
        return False

    try:
        await bot.send_message(chat_id=telegram_id, text=text, reply_markup=reply_markup)
        logger.info(f"Notification sent to technician {telegram_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send notification to {telegram_id}: {e}")
        return False


async def send_to_admin(
    telegram_id: int,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> bool:
    """
    Отправляет сообщение админу/диспетчеру.

    Args:
        telegram_id: Telegram ID админа
        text: Текст сообщения
        reply_markup: Опциональная клавиатура

    Returns:
        True если отправлено успешно, False при ошибке
    """
    return await send_to_technician(telegram_id, text, reply_markup)


async def notify_to_upcoming(
    telegram_id: int,
    apparatus_id: str,
    scheduled_at: str,
    days_before: int,
) -> bool:
    """
    Уведомление о предстоящем ТО (за 2 дня или в день).

    Args:
        telegram_id: Telegram ID техника
        apparatus_id: ID аппарата
        scheduled_at: Дата и время ТО (строка)
        days_before: За сколько дней уведомление (2 или 0)
    """
    if days_before == 2:
        text = (
            f"🔔 Напоминание: ТО запланировано через 2 дня\n\n"
            f"📍 Аппарат: {apparatus_id}\n"
            f"📅 Дата ТО: {scheduled_at}\n\n"
            f"Подготовьтесь к проведению технического обслуживания."
        )
        reply_markup = None
    else:  # days_before == 0 (день ТО)
        text = (
            f"🔔 Сегодня ТО!\n\n"
            f"📍 Аппарат: {apparatus_id}\n"
            f"📅 Запланировано: {scheduled_at}\n\n"
            f"Нажмите кнопку ниже, чтобы приступить к ТО (сканирование QR-кода)."
        )
        reply_markup = get_start_to_keyboard(apparatus_id)

    return await send_to_technician(telegram_id, text, reply_markup)


async def notify_to_overdue(
    telegram_id: int,
    apparatus_id: str,
    scheduled_at: str,
    task_id: UUID,
) -> bool:
    """
    Уведомление технику о просроченном ТО.

    Args:
        telegram_id: Telegram ID техника
        apparatus_id: ID аппарата
        scheduled_at: Дата планируемого ТО
        task_id: ID задания ТО
    """
    text = (
        f"⚠️ ВНИМАНИЕ: ТО просрочено!\n\n"
        f"📍 Аппарат: {apparatus_id}\n"
        f"📅 Должно было быть: {scheduled_at}\n"
        f"🆔 ID задания: {task_id}\n\n"
        f"Просьба выполнить ТО в ближайшее время или связаться с диспетчером."
    )
    return await send_to_technician(telegram_id, text)


async def notify_admin_overdue(
    telegram_id: int,
    apparatus_id: str,
    technician_name: str,
    scheduled_at: str,
    task_id: UUID,
) -> bool:
    """
    Уведомление админу/диспетчеру о просроченном ТО.

    Args:
        telegram_id: Telegram ID админа
        apparatus_id: ID аппарата
        technician_name: Имя техника
        scheduled_at: Дата планируемого ТО
        task_id: ID задания ТО
    """
    text = (
        f"🚨 ПРОСРОЧЕННОЕ ТО\n\n"
        f"📍 Аппарат: {apparatus_id}\n"
        f"👷 Техник: {technician_name}\n"
        f"📅 Планировалось: {scheduled_at}\n"
        f"🆔 ID задания: {task_id}\n\n"
        f"Требуется вмешательство диспетчера."
    )
    return await send_to_admin(telegram_id, text)


async def notify_to_accepted(
    telegram_id: int,
    apparatus_id: str,
    completed_at: str,
) -> bool:
    """
    Уведомление технику: ТО принято админом.

    Args:
        telegram_id: Telegram ID техника
        apparatus_id: ID аппарата
        completed_at: Дата завершения ТО
    """
    text = (
        f"✅ ТО принято!\n\n"
        f"📍 Аппарат: {apparatus_id}\n"
        f"📅 Завершено: {completed_at}\n\n"
        f"Отчёт проверен и принят администратором. Рейтинг обновлен."
    )
    return await send_to_technician(telegram_id, text)


async def notify_to_rejected(
    telegram_id: int,
    apparatus_id: str,
    reason: str,
    task_id: UUID,
) -> bool:
    """
    Уведомление технику: ТО возвращено на доработку.

    Args:
        telegram_id: Telegram ID техника
        apparatus_id: ID аппарата
        reason: Причина отклонения
        task_id: ID задания ТО
    """
    text = (
        f"❌ ТО возвращено на доработку\n\n"
        f"📍 Аппарат: {apparatus_id}\n"
        f"🆔 ID задания: {task_id}\n"
        f"📝 Причина: {reason}\n\n"
        f"Просьба устранить замечания и отправить отчёт повторно."
    )
    return await send_to_technician(telegram_id, text)


async def notify_cash_collection_scheduled(
    telegram_id: int,
    apparatus_id: str,
    scheduled_at: str,
) -> bool:
    """
    Уведомление о запланированной инкассации.

    Args:
        telegram_id: Telegram ID инкассатора/техника
        apparatus_id: ID аппарата
        scheduled_at: Дата и время инкассации
    """
    text = (
        f"💰 Инкассация запланирована\n\n"
        f"📍 Аппарат: {apparatus_id}\n"
        f"📅 Время: {scheduled_at}\n\n"
        f"Просьба прибуть к аппарату для изъятия наличных."
    )
    return await send_to_technician(telegram_id, text)


async def notify_emergency_dispatch(
    telegram_id: int,
    apparatus_id: str,
    issue_type: str,
    description: str,
    priority: str,
) -> bool:
    """
    Уведомление о аварийном выезде.

    Args:
        telegram_id: Telegram ID техника
        apparatus_id: ID аппарата
        issue_type: Тип проблемы
        description: Описание проблемы
        priority: Приоритет (high/medium/low)
    """
    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")

    text = (
        f"{priority_emoji} АВАРИЙНЫЙ ВЫЕЗД ({priority.upper()})\n\n"
        f"📍 Аппарат: {apparatus_id}\n"
        f"🔧 Проблема: {issue_type}\n"
        f"📝 Описание: {description}\n\n"
        f"Требуется срочный выезд!"
    )
    return await send_to_technician(telegram_id, text)