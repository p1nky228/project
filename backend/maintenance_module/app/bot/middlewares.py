"""
Middleware для бота ТО (технического обслуживания).
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.apparatus import Apparatus
from app.models.technician import Technician, TechnicianRole


class TechnicianAuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки, что пользователь — активный техник.

    Проверяет:
    - Пользователь существует в БД
    - Роль = technician
    - is_active = True

    Сохраняет объект technician в data["technician"] для использования в хендлерах.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем telegram_id из события
        telegram_id = None
        if isinstance(event, Message):
            telegram_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            telegram_id = event.from_user.id
        elif isinstance(event, Update):
            if event.message:
                telegram_id = event.message.from_user.id
            elif event.callback_query:
                telegram_id = event.callback_query.from_user.id

        if telegram_id is None:
            # Не наше событие, пропускаем
            return await handler(event, data)

        # Ищем техника в БД
        async with async_session_maker() as session:
            stmt = select(Technician).where(
                Technician.telegram_id == telegram_id,
                Technician.role == TechnicianRole.TECHNICIAN,
                Technician.is_active == True  # noqa: E712
            )
            result = await session.execute(stmt)
            technician = result.scalar_one_or_none()

        if technician is None:
            # Не техник или неактивен - отправляем сообщение об ошибке
            if isinstance(event, Message):
                await event.answer(
                    "❌ Доступ запрещен. Вы не являетесь активным техником."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "❌ Доступ запрещен. Вы не являетесь активным техником.",
                    show_alert=True
                )
            return

        # Сохраняем техника в data для хендлеров
        data["technician"] = technician
        return await handler(event, data)


class ApparatusBindMiddleware(BaseMiddleware):
    """
    Middleware для привязки аппарата к FSM при сканировании QR-кода.

    Проверяет:
    - Аппарат существует
    - Аппарат закреплен за этим техником (через apparatus_technician M2M или technician_id)

    Сохраняет apparatus_id и apparatus в data для FSM.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Этот middleware срабатывает только для callback_query с apparatus_id
        if not isinstance(event, CallbackQuery):
            return await handler(event, data)

        # Проверяем, что это callback для начала ТО или сканирования QR
        callback_data = event.data or ""
        if not (callback_data.startswith("start_to_") or callback_data.startswith("qr_scan_")):
            return await handler(event, data)

        # Извлекаем apparatus_id из callback_data
        # Формат: start_to_{apparatus_id} или qr_scan_{apparatus_id}
        parts = callback_data.split("_")
        if len(parts) < 3:
            return await handler(event, data)

        apparatus_id_str = "_".join(parts[2:])  # На случай если UUID содержит подчеркивания

        # Получаем техника из data (должен быть установлен TechnicianAuthMiddleware)
        technician = data.get("technician")
        if not technician:
            await event.answer("❌ Ошибка авторизации. Попробуйте снова.", show_alert=True)
            return

        # Проверяем аппарат и назначение в одной сессии
        async with async_session_maker() as session:
            from uuid import UUID
            from sqlalchemy import select
            from app.models.technician import apparatus_technician

            try:
                apparatus_uuid = UUID(apparatus_id_str)
            except ValueError:
                await event.answer("❌ Неверный ID аппарата.", show_alert=True)
                return

            stmt = select(Apparatus).where(Apparatus.id == apparatus_uuid)
            result = await session.execute(stmt)
            apparatus = result.scalar_one_or_none()

            if apparatus is None:
                await event.answer("❌ Аппарат не найден.", show_alert=True)
                return

            # Проверяем, закреплен ли аппарат за техником
            # Проверяем через M2M связь apparatus_technician ИЛИ через прямой technician_id
            is_assigned = False
            if apparatus.technician_id == technician.id:
                is_assigned = True
            else:
                # Проверяем M2M связь в той же сессии
                stmt = select(apparatus_technician).where(
                    apparatus_technician.c.apparatus_id == apparatus.id,
                    apparatus_technician.c.technician_id == technician.id
                )
                result = await session.execute(stmt)
                is_assigned = result.first() is not None

        if not is_assigned:
            await event.answer(
                "❌ Этот аппарат не закреплен за вами. Обратитесь к диспетчеру.",
                show_alert=True
            )
            return

        # Сохраняем в data для FSM
        data["apparatus_id"] = str(apparatus.id)
        data["apparatus"] = apparatus

        return await handler(event, data)