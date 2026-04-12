"""Репозиторий для работы с учебными планами и сессиями."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.study import (
    StudyCheckpoint,
    StudyChecklistItem,
    StudyModule,
    StudyPlan,
    StudySession,
)
from app.repositories.base import BaseRepository


class StudyRepository(BaseRepository[StudyPlan]):
    """Репозиторий учебных планов пользователя."""

    def _load_plan_query(self, user_id: UUID):
        """Базовый запрос плана с жадной загрузкой связей."""
        return (
            select(StudyPlan)
            .where(StudyPlan.user_id == user_id)
            .options(
                selectinload(StudyPlan.checkpoints),
                selectinload(StudyPlan.checklist_items),
                selectinload(StudyPlan.sessions),
                selectinload(StudyPlan.modules),
            )
            .order_by(StudyPlan.created_at.desc())
        )

    async def list_plans(self, user_id: UUID) -> list[StudyPlan]:
        """Возвращает все планы пользователя с загрузкой связей."""
        result = await self._session.execute(self._load_plan_query(user_id))
        return list(result.scalars().all())

    async def get_plan_by_id(self, user_id: UUID, plan_id: UUID) -> StudyPlan | None:
        """Возвращает план по ID в пределах библиотеки пользователя."""
        result = await self._session.execute(
            self._load_plan_query(user_id).where(StudyPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def refresh_plan(self, plan_id: UUID) -> StudyPlan | None:
        """Перезагружает план по ID без фильтра по пользователю (внутренний вызов)."""
        result = await self._session.execute(
            select(StudyPlan)
            .where(StudyPlan.id == plan_id)
            .options(
                selectinload(StudyPlan.checkpoints),
                selectinload(StudyPlan.checklist_items),
                selectinload(StudyPlan.sessions),
                selectinload(StudyPlan.modules),
            )
        )
        return result.scalar_one_or_none()

    async def get_checkpoint_by_id(
        self, user_id: UUID, checkpoint_id: UUID
    ) -> StudyCheckpoint | None:
        """Возвращает тему (checkpoint) по ID — только если план принадлежит пользователю."""
        result = await self._session.execute(
            select(StudyCheckpoint)
            .join(StudyPlan, StudyPlan.id == StudyCheckpoint.plan_id)
            .where(StudyCheckpoint.id == checkpoint_id)
            .where(StudyPlan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_checklist_item_by_id(
        self, user_id: UUID, item_id: UUID
    ) -> StudyChecklistItem | None:
        """Возвращает элемент чеклиста по ID — только если план принадлежит пользователю."""
        result = await self._session.execute(
            select(StudyChecklistItem)
            .join(StudyPlan, StudyPlan.id == StudyChecklistItem.plan_id)
            .where(StudyChecklistItem.id == item_id)
            .where(StudyPlan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_module_by_id(
        self, user_id: UUID, module_id: UUID
    ) -> StudyModule | None:
        """Возвращает модуль по ID — только если план принадлежит пользователю."""
        result = await self._session.execute(
            select(StudyModule)
            .join(StudyPlan, StudyPlan.id == StudyModule.plan_id)
            .where(StudyModule.id == module_id)
            .where(StudyPlan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_active_session_for_user(
        self, user_id: UUID
    ) -> StudySession | None:
        """Возвращает активную (незавершённую) сессию пользователя среди всех планов."""
        result = await self._session.execute(
            select(StudySession)
            .join(StudyPlan, StudyPlan.id == StudySession.plan_id)
            .where(StudyPlan.user_id == user_id)
            .where(StudySession.ended_at.is_(None))
            .order_by(StudySession.started_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_active_session_for_plan(
        self, plan_id: UUID
    ) -> StudySession | None:
        """Возвращает активную сессию конкретного плана."""
        result = await self._session.execute(
            select(StudySession)
            .where(StudySession.plan_id == plan_id)
            .where(StudySession.ended_at.is_(None))
            .order_by(StudySession.started_at.desc())
        )
        return result.scalar_one_or_none()

    async def list_sessions(self, plan_id: UUID) -> list[StudySession]:
        """Возвращает все сессии плана, упорядоченные по дате начала (новые первыми)."""
        result = await self._session.execute(
            select(StudySession)
            .where(StudySession.plan_id == plan_id)
            .order_by(StudySession.started_at.desc())
        )
        return list(result.scalars().all())

    async def save(self, plan: StudyPlan) -> StudyPlan:
        """Сохраняет план и возвращает обновлённое состояние."""
        self._session.add(plan)
        await self._session.commit()
        await self._session.refresh(plan)
        return plan

    async def update(self, plan: StudyPlan) -> StudyPlan:
        """Коммитит изменения плана."""
        await self._session.commit()
        await self._session.refresh(plan)
        return plan

    async def delete(self, plan: StudyPlan) -> None:
        """Удаляет план из БД."""
        await self._session.delete(plan)
        await self._session.commit()

    async def flush(self) -> None:
        """Сбрасывает отложенные операции в БД без коммита."""
        await self._session.flush()
