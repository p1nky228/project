"""
Admin API routes for the Maintenance Module.

Endpoints:
- GET /admin/tasks - List TO tasks with filters
- GET /admin/tasks/{task_id} - Get task details with presigned photo URLs
- POST /admin/tasks/{task_id}/accept - Accept completed TO task
- POST /admin/tasks/{task_id}/reject - Reject TO task (return for revision)
- GET /admin/technicians - List technicians with ratings
- GET /admin/apparatuses - List apparatuses with status
- GET /admin/stats - Get dashboard statistics
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_async_session
from app.models.apparatus import Apparatus, ApparatusStatus
from app.models.technician import Technician, TechnicianRole
from app.models.to_task import TOTask, TOTaskStatus
from app.models.to_photo import TOPhoto
from app.services import get_minio_client
from app.core.config import settings
from fastapi import Header

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_current_admin(
    x_admin_key: str = Header(..., alias="X-Admin-Key"),
) -> dict:
    """
    Admin authentication via API key header.

    Requires X-Admin-Key header matching ADMIN_API_KEY from settings.
    For production, replace with JWT-based authentication.
    """
    if not settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API not configured. Set ADMIN_API_KEY in environment."
        )
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key"
        )
    return {"id": "admin", "role": "admin"}


# ============================================================================
# TASKS ENDPOINTS
# ============================================================================

@router.get("/tasks")
async def list_tasks(
    status: Optional[TOTaskStatus] = Query(None, description="Filter by task status"),
    technician_id: Optional[UUID] = Query(None, description="Filter by technician"),
    apparatus_id: Optional[UUID] = Query(None, description="Filter by apparatus"),
    date_from: Optional[datetime] = Query(None, description="Filter by scheduled date from"),
    date_to: Optional[datetime] = Query(None, description="Filter by scheduled date to"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Получить список заданий ТО с фильтрами и пагинацией.

    Args:
        status: Статус задания (pending, in_progress, completed, rejected, overdue)
        technician_id: ID техника
        apparatus_id: ID аппарата
        date_from: Дата от (scheduled_at >= date_from)
        date_to: Дата до (scheduled_at <= date_to)
        page: Номер страницы (начиная с 1)
        page_size: Размер страницы (1-100)

    Returns:
        Пагинированный список заданий
    """
    # Базовый запрос с подгрузкой связей
    stmt = select(TOTask).options(
        selectinload(TOTask.apparatus),
        selectinload(TOTask.technician),
        selectinload(TOTask.photos),
    ).order_by(desc(TOTask.created_at))

    # Применяем фильтры
    filters = []
    if status:
        filters.append(TOTask.status == status)
    if technician_id:
        filters.append(TOTask.technician_id == technician_id)
    if apparatus_id:
        filters.append(TOTask.apparatus_id == apparatus_id)
    if date_from:
        filters.append(TOTask.scheduled_at >= date_from)
    if date_to:
        filters.append(TOTask.scheduled_at <= date_to)

    if filters:
        stmt = stmt.where(and_(*filters))

    # Подсчет общего количества
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar()

    # Пагинация
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await session.execute(stmt)
    tasks = result.scalars().all()

    # Формируем ответ
    task_list = []
    for task in tasks:
        task_list.append({
            "id": str(task.id),
            "apparatus_id": str(task.apparatus_id),
            "apparatus_address": task.apparatus.address if task.apparatus else None,
            "technician_id": str(task.technician_id),
            "technician_name": task.technician.full_name if task.technician else None,
            "status": task.status.value,
            "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "accepted_at": task.accepted_at.isoformat() if task.accepted_at else None,
            "rejected_at": task.rejected_at.isoformat() if task.rejected_at else None,
            "meter_readings": task.meter_readings,
            "cash_amount": float(task.cash_amount) if task.cash_amount else None,
            "comment": task.comment,
            "photos_count": len(task.photos),
            "created_at": task.created_at.isoformat() if task.created_at else None,
        })

    return {
        "items": task_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/tasks/{task_id}")
async def get_task_details(
    task_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Получить детали задания ТО с presigned URL для фото.

    Args:
        task_id: ID задания ТО

    Returns:
        Полная информация о задании с URL для фото
    """
    stmt = select(TOTask).options(
        selectinload(TOTask.apparatus),
        selectinload(TOTask.technician),
        selectinload(TOTask.photos),
    ).where(TOTask.id == task_id)

    result = await session.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Генерируем presigned URL для фото
    minio_client = get_minio_client()
    photos_with_urls = []

    for photo in task.photos:
        try:
            presigned_url = minio_client.get_file_url(photo.s3_key, expires=3600)
            photos_with_urls.append({
                "id": str(photo.id),
                "step_number": photo.step_number,
                "s3_key": photo.s3_key,
                "url": presigned_url,
                "created_at": photo.created_at.isoformat() if photo.created_at else None,
            })
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for photo {photo.id}: {e}")
            photos_with_urls.append({
                "id": str(photo.id),
                "step_number": photo.step_number,
                "s3_key": photo.s3_key,
                "url": None,
                "error": "Failed to generate URL",
            })

    return {
        "id": str(task.id),
        "apparatus_id": str(task.apparatus_id),
        "apparatus_address": task.apparatus.address if task.apparatus else None,
        "apparatus_lat": task.apparatus.lat if task.apparatus else None,
        "apparatus_lon": task.apparatus.lon if task.apparatus else None,
        "technician_id": str(task.technician_id),
        "technician_name": task.technician.full_name if task.technician else None,
        "technician_telegram_id": task.technician.telegram_id if task.technician else None,
        "status": task.status.value,
        "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "accepted_at": task.accepted_at.isoformat() if task.accepted_at else None,
        "rejected_at": task.rejected_at.isoformat() if task.rejected_at else None,
        "meter_readings": task.meter_readings,
        "cash_amount": float(task.cash_amount) if task.cash_amount else None,
        "comment": task.comment,
        "photos": photos_with_urls,
        "photos_json": task.photos_json,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


@router.post("/tasks/{task_id}/accept")
async def accept_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Принять выполненное ТО (статус остается COMPLETED, записывается время принятия).

    Args:
        task_id: ID задания ТО

    Returns:
        Обновленное задание
    """
    stmt = select(TOTask).options(
        selectinload(TOTask.technician),
        selectinload(TOTask.apparatus),
    ).where(TOTask.id == task_id)

    result = await session.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.status != TOTaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task must be in COMPLETED status to accept, current: {task.status.value}"
        )

    # Записываем время принятия админом (не перезаписываем completed_at - это время завершения техником)
    task.accepted_at = datetime.now()
    await session.commit()
    await session.refresh(task)

    # TODO: Уведомить техника через NotificationService
    # from app.services import notify_to_accepted
    # if task.technician and task.technician.telegram_id:
    #     await notify_to_accepted(
    #         telegram_id=task.technician.telegram_id,
    #         apparatus_id=str(task.apparatus_id),
    #         completed_at=task.completed_at.strftime('%d.%m.%Y %H:%M'),
    #     )

    logger.info(f"Admin {admin['id']} accepted task {task_id}")

    return {
        "id": str(task.id),
        "status": task.status.value,
        "accepted_at": task.accepted_at.isoformat() if task.accepted_at else None,
        "message": "Task accepted successfully"
    }


@router.post("/tasks/{task_id}/reject")
async def reject_task(
    task_id: UUID,
    reason: str = Query(..., min_length=1, max_length=500, description="Reason for rejection"),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Вернуть ТО на доработку (меняет статус на REJECTED, записывается время отклонения).

    Args:
        task_id: ID задания ТО
        reason: Причина отклонения

    Returns:
        Обновленное задание
    """
    stmt = select(TOTask).options(
        selectinload(TOTask.technician),
        selectinload(TOTask.apparatus),
    ).where(TOTask.id == task_id)

    result = await session.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task.status not in [TOTaskStatus.COMPLETED, TOTaskStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task must be in COMPLETED or IN_PROGRESS status to reject, current: {task.status.value}"
        )

    # Меняем статус на REJECTED
    task.status = TOTaskStatus.REJECTED
    task.comment = (task.comment or "") + f"\n\n[Отклонено админом: {reason}]"
    # Записываем время отклонения (не перезаписываем completed_at)
    task.rejected_at = datetime.now()
    await session.commit()
    await session.refresh(task)

    # TODO: Уведомить техника через NotificationService
    # from app.services import notify_to_rejected
    # if task.technician and task.technician.telegram_id:
    #     await notify_to_rejected(
    #         telegram_id=task.technician.telegram_id,
    #         apparatus_id=str(task.apparatus_id),
    #         reason=reason,
    #         task_id=task.id,
    #     )

    logger.info(f"Admin {admin['id']} rejected task {task_id}: {reason}")

    return {
        "id": str(task.id),
        "status": task.status.value,
        "rejected_at": task.rejected_at.isoformat() if task.rejected_at else None,
        "reason": reason,
        "message": "Task rejected successfully"
    }


# ============================================================================
# TECHNICIANS ENDPOINTS
# ============================================================================

@router.get("/technicians")
async def list_technicians(
    role: Optional[TechnicianRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Получить список техников с рейтингами.

    Args:
        role: Роль (technician, admin, dispatcher, manager)
        is_active: Только активные
        page: Номер страницы
        page_size: Размер страницы

    Returns:
        Пагинированный список техников
    """
    stmt = select(Technician).order_by(desc(Technician.rating))

    filters = []
    if role:
        filters.append(Technician.role == role)
    if is_active is not None:
        filters.append(Technician.is_active == is_active)

    if filters:
        stmt = stmt.where(and_(*filters))

    # Подсчет
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar()

    # Пагинация
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await session.execute(stmt)
    technicians = result.scalars().all()

    tech_list = []
    for tech in technicians:
        # Считаем статистику заданий за 30 дней
        since = datetime.now() - timedelta(days=30)
        task_stmt = select(func.count(TOTask.id)).where(
            TOTask.technician_id == tech.id,
            TOTask.created_at >= since,
        )
        task_count_result = await session.execute(task_stmt)
        tasks_30d = task_count_result.scalar() or 0

        completed_stmt = select(func.count(TOTask.id)).where(
            TOTask.technician_id == tech.id,
            TOTask.status == TOTaskStatus.COMPLETED,
            TOTask.completed_at >= since,
        )
        completed_result = await session.execute(completed_stmt)
        completed_30d = completed_result.scalar() or 0

        tech_list.append({
            "id": str(tech.id),
            "telegram_id": tech.telegram_id,
            "full_name": tech.full_name,
            "role": tech.role.value,
            "rating": tech.rating,
            "is_active": tech.is_active,
            "tasks_30d": tasks_30d,
            "completed_30d": completed_30d,
            "created_at": tech.created_at.isoformat() if tech.created_at else None,
        })

    return {
        "items": tech_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/technicians/{technician_id}")
async def get_technician_details(
    technician_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Получить детали техника с историей заданий.

    Args:
        technician_id: ID техника

    Returns:
        Детальная информация о технике
    """
    stmt = select(Technician).where(Technician.id == technician_id)
    result = await session.execute(stmt)
    tech = result.scalar_one_or_none()

    if not tech:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician not found"
        )

    # Задания за последние 30 дней
    since = datetime.now() - timedelta(days=30)
    task_stmt = select(TOTask).where(
        TOTask.technician_id == tech.id,
        TOTask.created_at >= since,
    ).order_by(desc(TOTask.created_at))

    task_result = await session.execute(task_stmt)
    tasks = task_result.scalars().all()

    task_list = []
    for task in tasks:
        task_list.append({
            "id": str(task.id),
            "apparatus_id": str(task.apparatus_id),
            "status": task.status.value,
            "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        })

    return {
        "id": str(tech.id),
        "telegram_id": tech.telegram_id,
        "full_name": tech.full_name,
        "role": tech.role.value,
        "rating": tech.rating,
        "is_active": tech.is_active,
        "tasks_30d": task_list,
        "created_at": tech.created_at.isoformat() if tech.created_at else None,
    }


# ============================================================================
# APPARATUSES ENDPOINTS
# ============================================================================

@router.get("/apparatuses")
async def list_apparatuses(
    status: Optional[ApparatusStatus] = Query(None, description="Filter by status"),
    technician_id: Optional[UUID] = Query(None, description="Filter by assigned technician"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Получить список аппаратов.

    Args:
        status: Статус аппарата (active, inactive, maintenance)
        technician_id: ID закрепленного техника
        page: Номер страницы
        page_size: Размер страницы

    Returns:
        Пагинированный список аппаратов
    """
    stmt = select(Apparatus).options(
        selectinload(Apparatus.technician),
    ).order_by(Apparatus.address)

    filters = []
    if status:
        filters.append(Apparatus.status == status)
    if technician_id:
        filters.append(Apparatus.technician_id == technician_id)

    if filters:
        stmt = stmt.where(and_(*filters))

    # Подсчет
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar()

    # Пагинация
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await session.execute(stmt)
    apparatuses = result.scalars().all()

    app_list = []
    for app in apparatuses:
        # Находим последнее ТО
        last_to_stmt = select(TOTask).where(
            TOTask.apparatus_id == app.id,
            TOTask.status == TOTaskStatus.COMPLETED,
        ).order_by(desc(TOTask.completed_at)).limit(1)

        last_to_result = await session.execute(last_to_stmt)
        last_to = last_to_result.scalar_one_or_none()

        # Проверяем, когда следующее ТО
        next_to_date = None
        if app.last_to_date:
            next_to_date = app.last_to_date + timedelta(days=app.to_interval_days)

        is_overdue = False
        if next_to_date and next_to_date < datetime.now() - timedelta(days=1):
            is_overdue = True

        app_list.append({
            "id": str(app.id),
            "address": app.address,
            "lat": app.lat,
            "lon": app.lon,
            "to_interval_days": app.to_interval_days,
            "last_to_date": app.last_to_date.isoformat() if app.last_to_date else None,
            "next_to_date": next_to_date.isoformat() if next_to_date else None,
            "is_overdue": is_overdue,
            "technician_id": str(app.technician_id) if app.technician_id else None,
            "technician_name": app.technician.full_name if app.technician else None,
            "status": app.status.value,
            "created_at": app.created_at.isoformat() if app.created_at else None,
        })

    return {
        "items": app_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


# ============================================================================
# STATS ENDPOINT
# ============================================================================

@router.get("/stats")
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_async_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Получить статистику для дашборда админа.

    Returns:
        Агрегированная статистика
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Всего аппаратов
    total_apparatuses = await session.execute(
        select(func.count(Apparatus.id))
    )
    total_apparatuses = total_apparatuses.scalar() or 0

    # Активных аппаратов
    active_apparatuses = await session.execute(
        select(func.count(Apparatus.id)).where(Apparatus.status == ApparatusStatus.ACTIVE)
    )
    active_apparatuses = active_apparatuses.scalar() or 0

    # Всего техников
    total_technicians = await session.execute(
        select(func.count(Technician.id)).where(Technician.role == TechnicianRole.TECHNICIAN)
    )
    total_technicians = total_technicians.scalar() or 0

    # Активных техников
    active_technicians = await session.execute(
        select(func.count(Technician.id)).where(
            and_(Technician.role == TechnicianRole.TECHNICIAN, Technician.is_active == True)  # noqa: E712
        )
    )
    active_technicians = active_technicians.scalar() or 0

    # Задания за сегодня
    tasks_today = await session.execute(
        select(func.count(TOTask.id)).where(TOTask.created_at >= today_start)
    )
    tasks_today = tasks_today.scalar() or 0

    # Задания за неделю
    tasks_week = await session.execute(
        select(func.count(TOTask.id)).where(TOTask.created_at >= week_start)
    )
    tasks_week = tasks_week.scalar() or 0

    # Задания за месяц
    tasks_month = await session.execute(
        select(func.count(TOTask.id)).where(TOTask.created_at >= month_start)
    )
    tasks_month = tasks_month.scalar() or 0

    # По статусам
    status_counts = {}
    for task_status in TOTaskStatus:
        count = await session.execute(
            select(func.count(TOTask.id)).where(TOTask.status == task_status)
        )
        status_counts[task_status.value] = count.scalar() or 0

    # Просроченные
    overdue_threshold = now - timedelta(days=1)
    overdue_count = await session.execute(
        select(func.count(TOTask.id)).where(
            and_(
                TOTask.status.in_([TOTaskStatus.PENDING, TOTaskStatus.IN_PROGRESS]),
                TOTask.scheduled_at < overdue_threshold,
            )
        )
    )
    overdue_count = overdue_count.scalar() or 0

    # Средний рейтинг
    avg_rating = await session.execute(
        select(func.avg(Technician.rating)).where(Technician.role == TechnicianRole.TECHNICIAN)
    )
    avg_rating = round(avg_rating.scalar() or 0, 1)

    # Топ техников по рейтингу
    top_tech_stmt = select(Technician).where(
        Technician.role == TechnicianRole.TECHNICIAN
    ).order_by(desc(Technician.rating)).limit(5)

    top_tech_result = await session.execute(top_tech_stmt)
    top_technicians = top_tech_result.scalars().all()

    top_tech_list = [{
        "id": str(t.id),
        "full_name": t.full_name,
        "rating": t.rating,
    } for t in top_technicians]

    return {
        "apparatuses": {
            "total": total_apparatuses,
            "active": active_apparatuses,
            "inactive": total_apparatuses - active_apparatuses,
        },
        "technicians": {
            "total": total_technicians,
            "active": active_technicians,
            "avg_rating": avg_rating,
            "top_5": top_tech_list,
        },
        "tasks": {
            "today": tasks_today,
            "this_week": tasks_week,
            "this_month": tasks_month,
            "by_status": status_counts,
            "overdue": overdue_count,
        },
    }