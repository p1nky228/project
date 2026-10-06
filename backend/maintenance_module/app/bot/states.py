"""
FSM состояния для чек-листа ТО (технического обслуживания).
"""

from aiogram.fsm.state import State, StatesGroup


class TOChecklistStates(StatesGroup):
    """
    Состояния FSM для прохождения чек-листа ТО.

    Порядок состояний:
    1. SCAN_QR - Ожидание QR-кода (callback query с apparatus_id)
    2. PHOTO_1_GENERAL - Фото общего вида аппарата
    3. PHOTO_2_DISPENSER - Фото узла розлива
    4. PHOTO_3_FILTERS - Фото фильтров с этикетками
    5. METER_READINGS - Показания счетчиков (опционально)
    6. CASH_AMOUNT - Сумма инкассации
    7. PHOTO_CASH - Фото изъятых денег
    8. COMMENT - Комментарий (опционально)
    9. COMPLETED - Завершено
    """

    SCAN_QR = State()               # Ожидание QR-кода (callback query с apparatus_id)
    PHOTO_1_GENERAL = State()       # Фото общего вида аппарата
    PHOTO_2_DISPENSER = State()     # Фото узла розлива
    PHOTO_3_FILTERS = State()       # Фото фильтров с этикетками
    METER_READINGS = State()        # Показания счетчиков (опционально)
    CASH_AMOUNT = State()           # Сумма инкассации
    PHOTO_CASH = State()            # Фото изъятых денег
    COMMENT = State()               # Комментарий (опционально)
    COMPLETED = State()             # Завершено