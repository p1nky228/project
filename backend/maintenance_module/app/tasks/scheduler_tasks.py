"""
APScheduler tasks for automated TO scheduling and notifications.

Jobs:
- check_upcoming_to (hourly): Find apparatuses due for TO within 2 days, create TOTask PENDING
- notify_2_days_before: Send Telegram notification to assigned technician
- notify_on_to_day: Send notification with "Start TO" button (triggers QR scan flow)
- check_overdue: Flag tasks overdue >1 day, notify admins/managers
"""

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.apparatus import Apparatus, ApparatusStatus
from app.models.technician import Technician, TechnicianRole
from app.models.to_task import TOTask, TOTaskStatus
from app.services import notify_to_upcoming, notify_admin_overdue, get_rating_service

logger = logging.getLogger(__name__)

# Глобальный экземпляр планировщика
_scheduler: Optional[AsyncIOScheduler] = None


async def get_scheduler() -> AsyncIOScheduler:
    """Возвращает глобальный экземпляр планировщика."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


async def init_scheduler() -> AsyncIOScheduler:
    """
    Инициализирует и запускает планировщик с заданиями.

    Returns:
        Запущенный AsyncIOScheduler
    """
    global _scheduler
    scheduler = await get_scheduler()

    # --- Ежечасная проверка предстоящих ТО ---
    scheduler.add_job(
        check_upcoming_to,
        CronTrigger(minute=0),  # Каждый час в XX:00
        id="check_upcoming_to",
        name="Check upcoming TO and create tasks",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # --- Уведомления за 2 дня до ТО (каждый день в 09:00) ---
    scheduler.add_job(
        notify_2_days_before,
        CronTrigger(hour=9, minute=0),
        id="notify_2_days_before",
        name="Notify technicians 2 days before TO",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # --- Уведомления в день ТО (каждый день в 08:00) ---
    scheduler.add_job(
        notify_on_to_day,
        CronTrigger(hour=8, minute=0),
        id="notify_on_to_day",
        name="Notify technicians on TO day with start button",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # --- Просроченные ТО (каждый день в 10:00) ---
    scheduler.add_job(
        check_overdue,
        CronTrigger(hour=10, minute=0),
        id="check_overdue",
        name="Check and flag overdue TO tasks",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # --- Ежедневная проверка рейтингов техников (каждый день в 00:30) ---
    scheduler.add_job(
        update_technician_ratings,
        CronTrigger(hour=0, minute=30),
        id="update_technician_ratings",
        name="Update technician ratings based on completed TO",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    logger.info("APScheduler started with jobs: check_upcoming_to, notify_2_days_before, notify_on_to_day, check_overdue, update_technician_ratings")
    return scheduler


async def shutdown_scheduler() -> None:
    """Останавливает планировщик при завершении приложения."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=True)
        logger.info("APScheduler stopped")


# ============================================================================
# JOB IMPLEMENTATIONS
# ============================================================================

async def check_upcoming_to() -> None:
    """
    Ежечасная задача: находит аппараты, у которых ТО должно быть проведено
    в ближайшие 2 дня, и создает TOTask со статусом PENDING.

    Логика:
    - last_to_date + to_interval_days <= now() + 2 дня
    - Аппарат должен быть ACTIVE
    - У аппарата должен быть закрепленный техник (technician_id или M2M)
    - Не должно быть уже существующего PENDING/IN_PROGRESS таска на этот аппарат

    Оптимизация: использует один SQL запрос с JOIN для фильтрации на уровне БД.
    """
    logger.info("Starting check_upcoming_to job")

    async with async_session_maker() as session:
        try:
            now = datetime.now()
            window_end = now + timedelta(days=2)

            # Подзапрос: аппараты с существующими PENDING/IN_PROGRESS тасками
            existing_tasks_subq = select(TOTask.apparatus_id).where(
                TOTask.status.in_([TOTaskStatus.PENDING, TOTaskStatus.IN_PROGRESS])
            ).subquery()

            # Подзапрос: technician_id для каждого аппарата (прямой technician_id ИЛИ M2M)
            # COALESCE берет первый не-NULL: прямой technician_id, иначе первый из M2M
            from sqlalchemy import func
            from app.models.technician import apparatus_technician

            tech_subq = select(
                Apparatus.id.label("apparatus_id"),
                func.coalesce(
                    Apparatus.technician_id,
                    select(apparatus_technician.c.technician_id)
                    .where(apparatus_technician.c.apparatus_id == Apparatus.id)
                    .limit(1)
                    .scalar_subquery()
                ).label("technician_id")
            ).where(
                Apparatus.status == ApparatusStatus.ACTIVE,
                Apparatus.last_to_date.is_not(None),
                # Фильтруем на уровне БД: next_to_date <= window_end
                (Apparatus.last_to_date + func.make_interval(days=Apparatus.to_interval_days)) <= window_end,
            ).subquery()

            # Основной запрос: получаем аппараты с техниками, у которых нет активных тасков
            stmt = select(
                tech_subq.c.apparatus_id,
                tech_subq.c.technician_id,
                Apparatus.last_to_date,
                Apparatus.to_interval_days,
            ).select_from(
                tech_subq.join(Apparatus, Apparatus.id == tech_subq.c.apparatus_id)
            ).where(
                tech_subq.c.technician_id.is_not(None),
                ~tech_subq.c.apparatus_id.in_(select(existing_tasks_subq.c.apparatus_id))
            )

            result = await session.execute(stmt)
            apparatuses_to_create = result.all()

            created_count = 0
            for app in apparatuses_to_create:
                next_to_date = app.last_to_date + timedelta(days=app.to_interval_days)

                to_task = TOTask(
                    apparatus_id=app.apparatus_id,
                    technician_id=app.technician_id,
                    status=TOTaskStatus.PENDING,
                    scheduled_at=next_to_date,
                )
                session.add(to_task)
                created_count += 1
                logger.info(f"Created TOTask {to_task.id} for apparatus {app.apparatus_id}, scheduled at {next_to_date}")

            await session.commit()
            logger.info(f"check_upcoming_to completed: created={created_count}, skipped=0 (filtered in DB)")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error in check_upcoming_to: {e}", exc_info=True)


async def notify_2_days_before() -> None:
    """
    Ежедневная задача (09:00): уведомляет техников о предстоящем ТО за 2 дня.

    Находит TOTask со статусом PENDING, где scheduled_at в диапазоне
    [now + 1 день, now + 2 дня], и отправляет уведомление технику.
    """
    logger.info("Starting notify_2_days_before job")

    async with async_session_maker() as session:
        try:
            now = datetime.now()
            window_start = now + timedelta(days=1)
            window_end = now + timedelta(days=2)

            # Join with Technician to avoid N+1 queries
            stmt = select(TOTask, Technician.telegram_id).join(
                Technician, TOTask.technician_id == Technician.id
            ).where(
                TOTask.status == TOTaskStatus.PENDING,
                TOTask.scheduled_at >= window_start,
                TOTask.scheduled_at <= window_end,
            )
            result = await session.execute(stmt)
            tasks_with_tech = result.all()

            notified_count = 0
            for task, telegram_id in tasks_with_tech:
                if telegram_id:
                    await notify_to_upcoming(
                        telegram_id=telegram_id,
                        apparatus_id=str(task.apparatus_id),
                        scheduled_at=task.scheduled_at.strftime('%d.%m.%Y %H:%M'),
                        days_before=2,
                    )
                    notified_count += 1
                else:
                    logger.warning(f"Technician {task.technician_id} has no telegram_id")

            logger.info(f"notify_2_days_before completed: notified {notified_count} technicians")

        except Exception as e:
            logger.error(f"Error in notify_2_days_before: {e}", exc_info=True)


async def notify_on_to_day() -> None:
    """
    Ежедневная задача (08:00): уведомляет техников о ТО на сегодня
    с кнопкой "Начать ТО" (триггерит QR scan flow).

    Находит TOTask со статусом PENDING, где scheduled_at в диапазоне
    [now, now + 1 день], и отправляет уведомление с inline кнопкой.
    """
    logger.info("Starting notify_on_to_day job")

    async with async_session_maker() as session:
        try:
            now = datetime.now()
            window_end = now + timedelta(days=1)

            # Join with Technician to avoid N+1 queries
            stmt = select(TOTask, Technician.telegram_id).join(
                Technician, TOTask.technician_id == Technician.id
            ).where(
                TOTask.status == TOTaskStatus.PENDING,
                TOTask.scheduled_at >= now,
                TOTask.scheduled_at <= window_end,
            )
            result = await session.execute(stmt)
            tasks_with_tech = result.all()

            notified_count = 0
            for task, telegram_id in tasks_with_tech:
                if telegram_id:
                    await notify_to_upcoming(
                        telegram_id=telegram_id,
                        apparatus_id=str(task.apparatus_id),
                        scheduled_at=task.scheduled_at.strftime('%d.%m.%Y %H:%M'),
                        days_before=0,  # 0 = день ТО, включает кнопку "Начать ТО"
                    )
                    notified_count += 1
                else:
                    logger.warning(f"Technician {task.technician_id} has no telegram_id")

            logger.info(f"notify_on_to_day completed: notified {notified_count} technicians")

        except Exception as e:
            logger.error(f"Error in notify_on_to_day: {e}", exc_info=True)


async def check_overdue() -> None:
    """
    Ежедневная задача (10:00): проверяет просроченные ТО.

    Находит TOTask со статусом PENDING/IN_PROGRESS, где scheduled_at < now() - 1 день.
    Меняет статус на OVERDUE и уведомляет админов/менеджеров.
    """
    logger.info("Starting check_overdue job")

    async with async_session_maker() as session:
        try:
            overdue_threshold = datetime.now() - timedelta(days=1)

            # Fetch tasks with technician data in a single query (avoid N+1)
            stmt = select(TOTask, Technician.full_name, Technician.telegram_id).join(
                Technician, TOTask.technician_id == Technician.id
            ).where(
                TOTask.status.in_([TOTaskStatus.PENDING, TOTaskStatus.IN_PROGRESS]),
                TOTask.scheduled_at < overdue_threshold,
            )
            result = await session.execute(stmt)
            tasks_with_tech = result.all()

            # Fetch admin telegram_ids once (not per task)
            admin_stmt = select(Technician.telegram_id).where(
                Technician.role.in_([TechnicianRole.ADMIN, TechnicianRole.DISPATCHER, TechnicianRole.MANAGER]),
                Technician.is_active == True,  # noqa: E712
            )
            admin_result = await session.execute(admin_stmt)
            admin_ids = admin_result.scalars().all()

            from app.services import notify_to_overdue, notify_admin_overdue

            overdue_count = 0
            for task, technician_name, technician_telegram_id in tasks_with_tech:
                task.status = TOTaskStatus.OVERDUE
                overdue_count += 1

                scheduled_str = task.scheduled_at.strftime('%d.%m.%Y %H:%M')
                apparatus_str = str(task.apparatus_id)

                # Уведомляем технику о просрочке
                if technician_telegram_id:
                    await notify_to_overdue(
                        telegram_id=technician_telegram_id,
                        apparatus_id=apparatus_str,
                        scheduled_at=scheduled_str,
                        task_id=task.id,
                    )

                # Уведомляем админов
                for admin_telegram_id in admin_ids:
                    await notify_admin_overdue(
                        telegram_id=admin_telegram_id,
                        apparatus_id=apparatus_str,
                        technician_name=technician_name or "Unknown",
                        scheduled_at=scheduled_str,
                        task_id=task.id,
                    )

            if overdue_count > 0:
                await session.commit()

            logger.info(f"check_overdue completed: flagged {overdue_count} tasks as OVERDUE")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error in check_overdue: {e}", exc_info=True)


async def update_technician_ratings() -> None:
    """
    Ежедневная задача (00:30): обновляет рейтинги техников на основе выполненных ТО.

    Использует RatingService для расчета рейтингов.
    """
    logger.info("Starting update_technician_ratings job")

    try:
        rating_service = get_rating_service()
        result = await rating_service.update_all_ratings()

        logger.info(f"update_technician_ratings completed: {result}")

    except Exception as e:
        logger.error(f"Error in update_technician_ratings: {e}", exc_info=True)


# ============================================================================
# MANUAL TRIGGERS (for testing/admin use)
# ============================================================================

async def run_check_upcoming_to_now() -> dict:
    """Ручной запуск check_upcoming_to для тестирования."""
    await check_upcoming_to()
    return {"status": "completed", "job": "check_upcoming_to"}


async def run_notify_2_days_before_now() -> dict:
    """Ручной запуск notify_2_days_before для тестирования."""
    await notify_2_days_before()
    return {"status": "completed", "job": "notify_2_days_before"}


async def run_notify_on_to_day_now() -> dict:
    """Ручной запуск notify_on_to_day для тестирования."""
    await notify_on_to_day()
    return {"status": "completed", "job": "notify_on_to_day"}


async def run_check_overdue_now() -> dict:
    """Ручной запуск check_overdue для тестирования."""
    await check_overdue()
    return {"status": "completed", "job": "check_overdue"}


async def run_update_ratings_now() -> dict:
    """Ручной запуск update_technician_ratings для тестирования."""
    await update_technician_ratings()
    return {"status": "completed", "job": "update_technician_ratings"}


def get_scheduler_status() -> dict:
    """Возвращает статус планировщика и список заданий."""
    global _scheduler
    if _scheduler is None:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })

    return {
        "running": _scheduler.running,
        "jobs": jobs,
    }