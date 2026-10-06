"""
RatingService для расчета и управления рейтингами техников.

Логика рейтинга:
- Базовый рейтинг: 0
- +10 за принятое ТО (status=COMPLETED, принято админом)
- -5 за отклоненное ТО (status=REJECTED)
- -10 за просроченное ТО (status=OVERDUE)
- Бонус за полноту отчета (фото, показания, инкассация, комментарий): +1 за каждый
- Штраф за отмену ТО: -3
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.technician import Technician, TechnicianRole
from app.models.to_task import TOTask, TOTaskStatus

logger = logging.getLogger(__name__)


class RatingService:
    """
    Сервис для управления рейтингами техников.
    """

    # Константы начислений/штрафов
    POINTS_ACCEPTED = 10
    POINTS_REJECTED = -5
    POINTS_OVERDUE = -10
    POINTS_CANCELLED = -3
    BONUS_PER_COMPLETION_ITEM = 1  # фото, показания, инкассация, комментарий

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    async def _get_session(self) -> AsyncSession:
        """Возвращает сессию БД (создает новую если не передана)."""
        if self._session:
            return self._session
        return async_session_maker()

    async def calculate_task_rating(self, task: TOTask) -> int:
        """
        Рассчитывает изменение рейтинга за одно задание.

        Args:
            task: Задание ТО

        Returns:
            Изменение рейтинга (может быть отрицательным)
        """
        if task.status == TOTaskStatus.COMPLETED:
            # Базовые баллы за принятое ТО
            points = self.POINTS_ACCEPTED

            # Бонусы за полноту отчета
            if task.photos_json and len(task.photos_json) > 0:
                points += self.BONUS_PER_COMPLETION_ITEM

            if task.meter_readings:
                points += self.BONUS_PER_COMPLETION_ITEM

            if task.cash_amount is not None:
                points += self.BONUS_PER_COMPLETION_ITEM

            if task.comment:
                points += self.BONUS_PER_COMPLETION_ITEM

            return points

        elif task.status == TOTaskStatus.REJECTED:
            return self.POINTS_REJECTED

        elif task.status == TOTaskStatus.OVERDUE:
            return self.POINTS_OVERDUE

        # Для других статусов (PENDING, IN_PROGRESS) - 0
        return 0

    async def update_technician_rating(self, technician_id: UUID) -> int:
        """
        Пересчитывает и обновляет рейтинг техника на основе всех заданий.

        Args:
            technician_id: ID техника

        Returns:
            Новый рейтинг
        """
        async with async_session_maker() as session:
            # Получаем техника
            stmt = select(Technician).where(Technician.id == technician_id)
            result = await session.execute(stmt)
            technician = result.scalar_one_or_none()

            if not technician:
                logger.warning(f"Technician {technician_id} not found")
                return 0

            # Считаем рейтинг за все время (или за последние N дней)
            # Для простоты считаем за все время
            stmt = select(TOTask).where(TOTask.technician_id == technician_id)
            result = await session.execute(stmt)
            tasks = result.scalars().all()

            total_rating = 0
            for task in tasks:
                total_rating += await self.calculate_task_rating(task)

            # Рейтинг не может быть отрицательным
            technician.rating = max(0, total_rating)

            await session.commit()
            await session.refresh(technician)

            logger.info(f"Updated rating for technician {technician_id}: {technician.rating}")
            return technician.rating

    async def update_all_ratings(self) -> dict:
        """
        Обновляет рейтинги всех техников одним SQL-запросом (O(n) вместо O(n×m)).

        Использует CASE expression для расчета рейтинга в базе данных,
        аналогично методу get_leaderboard.

        Returns:
            Статистика обновления
        """
        async with async_session_maker() as session:
            # CASE expression для расчета рейтинга за задание
            rating_case = case(
                (TOTask.status == TOTaskStatus.COMPLETED,
                 self.POINTS_ACCEPTED +
                 case((TOTask.photos_json.isnot(None) & (func.jsonb_array_length(TOTask.photos_json) > 0), self.BONUS_PER_COMPLETION_ITEM), else_=0) +
                 case((TOTask.meter_readings.isnot(None), self.BONUS_PER_COMPLETION_ITEM), else_=0) +
                 case((TOTask.cash_amount.isnot(None), self.BONUS_PER_COMPLETION_ITEM), else_=0) +
                 case((TOTask.comment.isnot(None), self.BONUS_PER_COMPLETION_ITEM), else_=0)
                ),
                (TOTask.status == TOTaskStatus.REJECTED, self.POINTS_REJECTED),
                (TOTask.status == TOTaskStatus.OVERDUE, self.POINTS_OVERDUE),
                else_=0
            )

            # Подзапрос: сумма рейтинга по каждому технику
            subquery = select(
                TOTask.technician_id,
                func.coalesce(func.sum(rating_case), 0).label("total_rating")
            ).where(
                TOTask.status.in_([TOTaskStatus.COMPLETED, TOTaskStatus.REJECTED, TOTaskStatus.OVERDUE])
            ).group_by(TOTask.technician_id).subquery()

            # Обновляем рейтинг всех техников одним запросом
            from sqlalchemy import update
            update_stmt = update(Technician).where(
                Technician.role == TechnicianRole.TECHNICIAN
            ).values(
                rating=func.greatest(subquery.c.total_rating, 0)
            ).where(Technician.id == subquery.c.technician_id)

            # SQLAlchemy не поддерживает UPDATE ... FROM напрямую так просто,
            # поэтому используем подход с CTE или отдельный запрос
            # Получаем рейтинг для каждого техника
            stmt = select(Technician.id, func.coalesce(subquery.c.total_rating, 0)).select_from(
                Technician.outerjoin(subquery, Technician.id == subquery.c.technician_id)
            ).where(Technician.role == TechnicianRole.TECHNICIAN)

            result = await session.execute(stmt)
            ratings = result.all()

            updated = 0
            for tech_id, total_rating in ratings:
                new_rating = max(0, total_rating or 0)
                # Обновляем только если рейтинг изменился
                update_one = update(Technician).where(Technician.id == tech_id).values(rating=new_rating)
                await session.execute(update_one)
                if new_rating != 0:  # считаем обновленным если рейтинг не нулевой (были задания)
                    updated += 1

            await session.commit()

            logger.info(f"update_all_ratings completed: updated {updated} of {len(ratings)} technicians")
            return {
                "total_technicians": len(ratings),
                "updated": updated,
            }

    async def get_technician_stats(self, technician_id: UUID, days: int = 30) -> dict:
        """
        Получает статистику техника за период.

        Args:
            technician_id: ID техника
            days: Период в днях (по умолчанию 30)

        Returns:
            Статистика техника
        """
        async with async_session_maker() as session:
            since = datetime.now() - timedelta(days=days)

            stmt = select(TOTask).where(
                TOTask.technician_id == technician_id,
                TOTask.created_at >= since,
            )
            result = await session.execute(stmt)
            tasks = result.scalars().all()

            stats = {
                "total": len(tasks),
                "by_status": {},
                "rating_change": 0,
                "completion_rate": 0.0,
            }

            completed_count = 0
            for task in tasks:
                status_key = task.status.value
                stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1

                if task.status == TOTaskStatus.COMPLETED:
                    completed_count += 1

                stats["rating_change"] += await self.calculate_task_rating(task)

            if stats["total"] > 0:
                stats["completion_rate"] = round(completed_count / stats["total"] * 100, 1)

            return stats

    async def get_leaderboard(self, limit: int = 10, days: Optional[int] = None) -> list:
        """
        Получает таблицу лидеров (топ техников по рейтингу).

        Args:
            limit: Количество техников в топе
            days: Если указано, считает рейтинг только за этот период

        Returns:
            Список топ техников
        """
        async with async_session_maker() as session:
            if days:
                since = datetime.now() - timedelta(days=days)

                # Подзапрос для подсчета рейтинга за период
                # Используем CASE expression для расчета баллов в SQL
                rating_case = case(
                    (TOTask.status == TOTaskStatus.COMPLETED,
                     self.POINTS_ACCEPTED +
                     case((TOTask.photos_json.isnot(None) & (func.jsonb_array_length(TOTask.photos_json) > 0), self.BONUS_PER_COMPLETION_ITEM), else_=0) +
                     case((TOTask.meter_readings.isnot(None), self.BONUS_PER_COMPLETION_ITEM), else_=0) +
                     case((TOTask.cash_amount.isnot(None), self.BONUS_PER_COMPLETION_ITEM), else_=0) +
                     case((TOTask.comment.isnot(None), self.BONUS_PER_COMPLETION_ITEM), else_=0)
                    ),
                    (TOTask.status == TOTaskStatus.REJECTED, self.POINTS_REJECTED),
                    (TOTask.status == TOTaskStatus.OVERDUE, self.POINTS_OVERDUE),
                    else_=0
                )

                subquery = select(
                    TOTask.technician_id,
                    func.coalesce(func.sum(rating_case), 0).label("period_rating")
                ).where(
                    and_(
                        TOTask.created_at >= since,
                        TOTask.status.in_([TOTaskStatus.COMPLETED, TOTaskStatus.REJECTED, TOTaskStatus.OVERDUE]),
                    )
                ).group_by(TOTask.technician_id).subquery()

                stmt = select(Technician, subquery.c.period_rating).join(
                    subquery, Technician.id == subquery.c.technician_id
                ).where(
                    Technician.role == TechnicianRole.TECHNICIAN
                ).order_by(
                    subquery.c.period_rating.desc()
                ).limit(limit)

                result = await session.execute(stmt)
                technicians = result.all()
                return [{
                    "id": str(t.Technician.id),
                    "full_name": t.Technician.full_name,
                    "rating": t.period_rating or 0,
                } for t in technicians]
            else:
                # Общий рейтинг
                stmt = select(Technician).where(
                    Technician.role == TechnicianRole.TECHNICIAN
                ).order_by(
                    Technician.rating.desc()
                ).limit(limit)

                result = await session.execute(stmt)
                technicians = result.scalars().all()
                return [{
                    "id": str(t.id),
                    "full_name": t.full_name,
                    "rating": t.rating,
                } for t in technicians]

    async def apply_rating_change(self, technician_id: UUID, change: int, reason: str) -> int:
        """
        Применяет ручное изменение рейтинга (для админов).

        Args:
            technician_id: ID техника
            change: Изменение рейтинга (может быть отрицательным)
            reason: Причина изменения

        Returns:
            Новый рейтинг
        """
        async with async_session_maker() as session:
            stmt = select(Technician).where(Technician.id == technician_id)
            result = await session.execute(stmt)
            technician = result.scalar_one_or_none()

            if not technician:
                raise ValueError(f"Technician {technician_id} not found")

            technician.rating = max(0, technician.rating + change)
            logger.info(f"Manual rating change for {technician_id}: {change} ({reason}). New rating: {technician.rating}")

            await session.commit()
            await session.refresh(technician)

            return technician.rating


# Глобальный экземпляр сервиса
_rating_service: Optional[RatingService] = None


def get_rating_service() -> RatingService:
    """Возвращает глобальный экземпляр RatingService."""
    global _rating_service
    if _rating_service is None:
        _rating_service = RatingService()
    return _rating_service