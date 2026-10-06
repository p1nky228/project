"""
Клавиатуры для бота ТО (технического обслуживания).
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_start_to_keyboard(apparatus_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой "Приступить к ТО".

    Args:
        apparatus_id: ID аппарата для начала ТО

    Returns:
        InlineKeyboardMarkup с кнопкой начала ТО
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔧 Приступить к ТО",
        callback_data=f"start_to_{apparatus_id}"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_photo_keyboard(step: int, total_steps: int, is_optional: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура для этапов с фото.

    Args:
        step: Текущий номер шага (1-based)
        total_steps: Общее количество шагов с фото
        is_optional: Является ли шаг опциональным (можно пропустить)

    Returns:
        InlineKeyboardMarkup с кнопками навигации
    """
    builder = InlineKeyboardBuilder()

    # Кнопка "Переснять" - удаляет последнее фото и возвращается к загрузке
    builder.button(
        text="🔄 Переснять",
        callback_data=f"retake_photo_{step}"
    )

    # Кнопка "Пропустить" для опциональных шагов
    if is_optional:
        builder.button(
            text="⏭ Пропустить",
            callback_data=f"skip_photo_{step}"
        )

    # Кнопка "Далее" - переход к следующему шагу
    if step < total_steps:
        builder.button(
            text="➡️ Далее",
            callback_data=f"next_photo_{step}"
        )
    else:
        builder.button(
            text="✅ Завершить фото",
            callback_data="finish_photos"
        )

    builder.adjust(2 if is_optional else 1)
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения завершения ТО.

    Returns:
        InlineKeyboardMarkup с кнопками подтверждения
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить завершение",
        callback_data="confirm_complete_to"
    )
    builder.button(
        text="🔙 Вернуться к комментарию",
        callback_data="back_to_comment"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_admin_review_keyboard(task_id: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для админа: принять или вернуть ТО на доработку.

    Args:
        task_id: ID задания ТО

    Returns:
        InlineKeyboardMarkup с кнопками модерации
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Принять",
        callback_data=f"accept_to_{task_id}"
    )
    builder.button(
        text="❌ Вернуть на доработку",
        callback_data=f"reject_to_{task_id}"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой отмены/выхода из FSM.

    Returns:
        InlineKeyboardMarkup с кнопкой отмены
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отменить ТО",
        callback_data="cancel_to"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_skip_optional_keyboard(callback_data: str = "skip_optional") -> InlineKeyboardMarkup:
    """
    Клавиатура для пропуска опционального шага.

    Args:
        callback_data: Данные для callback кнопки "Пропустить"

    Returns:
        InlineKeyboardMarkup с кнопкой пропуска
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏭ Пропустить",
        callback_data=callback_data
    )
    builder.button(
        text="❌ Отменить ТО",
        callback_data="cancel_to"
    )
    builder.adjust(1)
    return builder.as_markup()