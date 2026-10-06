"""
Инициализация пакета bot для модуля ТО.

Экспортирует:
- Состояния FSM (TOChecklistStates)
- Функции клавиатур
- Middleware классы
- Router с хендлерами
"""

from .states import TOChecklistStates
from .keyboards import (
    get_start_to_keyboard,
    get_photo_keyboard,
    get_confirm_keyboard,
    get_admin_review_keyboard,
    get_cancel_keyboard,
)
from .middlewares import TechnicianAuthMiddleware, ApparatusBindMiddleware
from .handlers import router

__all__ = [
    # States
    "TOChecklistStates",
    # Keyboards
    "get_start_to_keyboard",
    "get_photo_keyboard",
    "get_confirm_keyboard",
    "get_admin_review_keyboard",
    "get_cancel_keyboard",
    # Middlewares
    "TechnicianAuthMiddleware",
    "ApparatusBindMiddleware",
    # Router
    "router",
]