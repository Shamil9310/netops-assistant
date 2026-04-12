"""Репозиторий для рабочей таймерной зоны."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.work_timer import (
    WorkTimerInterruption,
    WorkTimerSession,
    WorkTimerTask,
)
from app.repositories.base import BaseRepository


class WorkTimerRepository(BaseRepository[WorkTimerTask]):
    """Репозиторий для задач, сессий и прерываний Work Timer."""

    def _load_task_query(self, user_id: UUID):
        return (
            select(WorkTimerTask)
            .where(WorkTimerTask.user_id == user_id)
            .options(
                selectinload(WorkTimerTask.sessions).selectinload(
                    WorkTimerSession.interruptions
                )
            )
            .order_by(WorkTimerTask.order_index.asc(), WorkTimerTask.created_at.desc())
        )

    async def list_tasks(self, user_id: UUID) -> list[WorkTimerTask]:
        result = await self._session.execute(self._load_task_query(user_id))
        return list(result.scalars().all())

    async def get_task_by_id(
        self, user_id: UUID, task_id: UUID
    ) -> WorkTimerTask | None:
        result = await self._session.execute(
            self._load_task_query(user_id).where(WorkTimerTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_task_by_id_unscoped(self, task_id: UUID) -> WorkTimerTask | None:
        result = await self._session.execute(
            select(WorkTimerTask)
            .where(WorkTimerTask.id == task_id)
            .options(
                selectinload(WorkTimerTask.sessions).selectinload(
                    WorkTimerSession.interruptions
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_session_for_user(
        self, user_id: UUID
    ) -> WorkTimerSession | None:
        result = await self._session.execute(
            select(WorkTimerSession)
            .join(WorkTimerTask, WorkTimerTask.id == WorkTimerSession.task_id)
            .where(WorkTimerTask.user_id == user_id)
            .where(WorkTimerSession.ended_at.is_(None))
            .order_by(WorkTimerSession.started_at.desc())
            .options(selectinload(WorkTimerSession.interruptions))
        )
        return result.scalar_one_or_none()

    async def get_active_session_for_task(
        self, task_id: UUID
    ) -> WorkTimerSession | None:
        result = await self._session.execute(
            select(WorkTimerSession)
            .where(WorkTimerSession.task_id == task_id)
            .where(WorkTimerSession.ended_at.is_(None))
            .order_by(WorkTimerSession.started_at.desc())
            .options(selectinload(WorkTimerSession.interruptions))
        )
        return result.scalar_one_or_none()

    async def list_sessions_for_week(
        self,
        user_id: UUID,
        week_start: datetime,
        week_end: datetime,
    ) -> list[WorkTimerSession]:
        result = await self._session.execute(
            select(WorkTimerSession)
            .join(WorkTimerTask, WorkTimerTask.id == WorkTimerSession.task_id)
            .where(WorkTimerTask.user_id == user_id)
            .where(WorkTimerSession.started_at >= week_start)
            .where(WorkTimerSession.started_at < week_end)
            .options(
                selectinload(WorkTimerSession.interruptions),
                selectinload(WorkTimerSession.task),
            )
            .order_by(WorkTimerSession.started_at.asc())
        )
        return list(result.scalars().all())

    async def save_task(self, task: WorkTimerTask) -> WorkTimerTask:
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def update_task(self, task: WorkTimerTask) -> WorkTimerTask:
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def delete_task(self, task: WorkTimerTask) -> None:
        await self._session.delete(task)
        await self._session.commit()

    async def save_session(self, session: WorkTimerSession) -> WorkTimerSession:
        self._session.add(session)
        await self._session.commit()
        await self._session.refresh(session)
        return session

    async def update_session(self, session: WorkTimerSession) -> WorkTimerSession:
        await self._session.commit()
        await self._session.refresh(session)
        return session

    async def save_interruption(
        self, interruption: WorkTimerInterruption
    ) -> WorkTimerInterruption:
        self._session.add(interruption)
        await self._session.commit()
        await self._session.refresh(interruption)
        return interruption

    async def update_interruption(
        self, interruption: WorkTimerInterruption
    ) -> WorkTimerInterruption:
        await self._session.commit()
        await self._session.refresh(interruption)
        return interruption
