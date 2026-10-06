"""
Минимальные хендлеры FSM для чек-листа ТО.

Содержит только Router, базовые переходы состояний и TODO для MinIO/БД.
Никаких реальных интеграций — только скелет.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, Location

from .states import TOChecklistStates

router = Router()

# --- Вход в ТО ---
@router.callback_query(F.data.startswith("start_to_"))
async def start_to_checklist(callback: CallbackQuery, state: FSMContext):
    """Callback 'start_to_{apparatus_id}' -> просим location, переход к PHOTO_1_GENERAL"""
    # TODO: извлечь apparatus_id из callback.data
    # TODO: проверить GPS (200м), создать TOTask в БД
    await state.set_state(TOChecklistStates.PHOTO_1_GENERAL)
    await callback.message.edit_text("📸 Шаг 1/6: Фото общего вида аппарата")
    await callback.answer()


# --- Фото шаги 1-3, 6 ---
@router.message(TOChecklistStates.PHOTO_1_GENERAL, F.photo)
@router.message(TOChecklistStates.PHOTO_2_DISPENSER, F.photo)
@router.message(TOChecklistStates.PHOTO_3_FILTERS, F.photo)
@router.message(TOChecklistStates.PHOTO_CASH, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    """Приём фото -> сохраняем file_id в state.data['photos'][step], переход к следующему"""
    # TODO: скачать фото, загрузить в MinIO, создать TOPhoto в БД
    current_state = await state.get_state()
    step_map = {
        "TOChecklistStates:PHOTO_1_GENERAL": 1,
        "TOChecklistStates:PHOTO_2_DISPENSER": 2,
        "TOChecklistStates:PHOTO_3_FILTERS": 3,
        "TOChecklistStates:PHOTO_CASH": 6,
    }
    step = step_map.get(current_state, 1)

    # Сохраняем file_id для последующей загрузки
    data = await state.get_data()
    photos = data.get("photos", {})
    photos[step] = message.photo[-1].file_id
    await state.update_data(photos=photos)

    # Переход к следующему состоянию
    next_states = {
        TOChecklistStates.PHOTO_1_GENERAL: TOChecklistStates.PHOTO_2_DISPENSER,
        TOChecklistStates.PHOTO_2_DISPENSER: TOChecklistStates.PHOTO_3_FILTERS,
        TOChecklistStates.PHOTO_3_FILTERS: TOChecklistStates.METER_READINGS,
        TOChecklistStates.PHOTO_CASH: TOChecklistStates.COMMENT,
    }
    next_state = next_states.get(await state.get_state())
    if next_state:
        await state.set_state(next_state)
        # TODO: правильный текст для каждого шага
        step_texts = {
            TOChecklistStates.PHOTO_2_DISPENSER: "📸 Шаг 2/6: Фото узла розлива",
            TOChecklistStates.PHOTO_3_FILTERS: "📸 Шаг 3/6: Фото фильтров с этикетками",
            TOChecklistStates.METER_READINGS: "📊 Введите показания счетчиков (или нажмите 'Пропустить')",
            TOChecklistStates.COMMENT: "✅ ТО завершено! Добавьте комментарий (или нажмите 'Пропустить')",
        }
        await message.answer(step_texts.get(next_state, "Следующий шаг"))

    # TODO: загрузить фото в MinIO, создать TOPhoto запись


# --- Навигация по фото (переснять/пропустить/далее) ---
@router.callback_query(F.data.startswith("retake_photo_"))
async def retake_photo(callback: CallbackQuery, state: FSMContext):
    """Удалить последнее фото из state.data['photos']"""
    # TODO: удалить из MinIO
    step = int(callback.data.split("_")[-1])
    data = await state.get_data()
    photos = data.get("photos", {})
    if step in photos:
        del photos[step]
        await state.update_data(photos=photos)
    await callback.answer("🔄 Переснимайте")


@router.callback_query(F.data.startswith("skip_photo_"))
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    """Пропуск опционального фото-шага"""
    step = int(callback.data.split("_")[-1])
    # TODO: логика пропуска фото
    await callback.answer(f"Шаг {step} пропущен")


@router.callback_query(F.data.startswith("next_photo_"))
async def next_photo(callback: CallbackQuery, state: FSMContext):
    """Переход к следующему фото-шагу без загрузки фото (если опционально)"""
    step = int(callback.data.split("_")[-1])
    # TODO: логика перехода
    await callback.answer(f"Переход к шагу {step + 1}")


@router.callback_query(F.data == "finish_photos")
async def finish_photos(callback: CallbackQuery, state: FSMContext):
    """Завершение фото-этапа -> переход к показаниям счетчиков"""
    await state.set_state(TOChecklistStates.METER_READINGS)
    await callback.message.edit_text("📊 Введите показания счетчиков (или нажмите 'Пропустить')")
    await callback.answer()


# --- Опциональные шаги ---
@router.message(TOChecklistStates.METER_READINGS, F.text)
async def handle_meter_readings(message: Message, state: FSMContext):
    """Показания счетчиков -> переход к CASH_AMOUNT"""
    await state.update_data(meter_readings=message.text)
    await state.set_state(TOChecklistStates.CASH_AMOUNT)
    await message.answer("💰 Введите сумму инкассации:")


@router.callback_query(F.data == "skip_optional", TOChecklistStates.METER_READINGS)
async def skip_meter_readings(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TOChecklistStates.CASH_AMOUNT)
    await callback.message.edit_text("💰 Введите сумму инкассации:")
    await callback.answer()


# --- Сумма инкассации ---
@router.message(TOChecklistStates.CASH_AMOUNT, F.text)
async def handle_cash_amount(message: Message, state: FSMContext):
    await state.update_data(cash_amount=message.text)
    await state.set_state(TOChecklistStates.PHOTO_CASH)
    await message.answer("📸 Шаг 6/6: Фото изъятых денег:")


# --- Комментарий ---
@router.message(TOChecklistStates.COMMENT, F.text)
async def handle_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await state.set_state(TOChecklistStates.COMPLETED)
    await message.answer("✅ ТО завершено! Нажмите 'Завершить ТО'")


@router.callback_query(F.data == "skip_optional", TOChecklistStates.COMMENT)
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TOChecklistStates.COMPLETED)
    await callback.message.edit_text("✅ ТО завершено! Нажмите 'Завершить ТО'")
    await callback.answer()


# --- Завершение ---
@router.callback_query(F.data == "confirm_complete_to", TOChecklistStates.COMPLETED)
async def complete_to(callback: CallbackQuery, state: FSMContext):
    """Сбор данных, обновление TOTask в БД, уведомление админа"""
    # TODO: собрать data, обновить TOTask (photos_json, meter_readings, cash_amount, comment, status=COMPLETED)
    # TODO: загрузить все фото в MinIO, создать TOPhoto записи
    # TODO: notification_service.send_to_admins(...)
    await state.clear()
    await callback.message.edit_text("✅ Отчёт отправлен на проверку администратору!")
    await callback.answer()


@router.callback_query(F.data == "back_to_comment", TOChecklistStates.COMPLETED)
async def back_to_comment(callback: CallbackQuery, state: FSMContext):
    """Вернуться к редактированию комментария"""
    await state.set_state(TOChecklistStates.COMMENT)
    await callback.message.edit_text("📝 Введите комментарий:")
    await callback.answer()


# --- Отмена ---
@router.callback_query(F.data == "cancel_to")
async def cancel_to(callback: CallbackQuery, state: FSMContext):
    """Удалить TOTask, фото из MinIO"""
    # TODO: cleanup
    await state.clear()
    await callback.message.edit_text("❌ ТО отменено")
    await callback.answer()


# --- GPS обработка ---
@router.message(F.location)
async def handle_location(message: Message, state: FSMContext):
    """Получение GPS от пользователя -> проверка 200м -> переход к фото"""
    # TODO: validate_gps, создать TOTask, переход к PHOTO_1_GENERAL
    await message.answer("📍 GPS получен. 📸 Шаг 1/6: Фото общего вида аппарата")
    await state.set_state(TOChecklistStates.PHOTO_1_GENERAL)