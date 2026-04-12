"""Репозиторий для работы с планами ночных работ."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.night_work import (
    NightWorkBlock,
    NightWorkPlan,
    NightWorkPlanStatus,
    NightWorkStep,
)
from app.repositories.base import BaseRepository


class NightWorkRepository(BaseRepository[NightWorkPlan]):
    """Репозиторий планов ночных работ."""

    def _load_plan_query(self):
        """Базовый запрос плана с жадной загрузкой блоков и шагов."""
        return select(NightWorkPlan).options(
            selectinload(NightWorkPlan.blocks).selectinload(NightWorkBlock.steps)
        )

    async def list_plans(
        self,
        user_id: UUID,
        status: NightWorkPlanStatus | None = None,
    ) -> list[NightWorkPlan]:
        """Возвращает планы ночных работ пользователя с необязательным фильтром статуса."""
        query = (
            self._load_plan_query()
            .where(NightWorkPlan.user_id == user_id)
            .order_by(NightWorkPlan.created_at.desc())
        )
        if status is not None:
            query = query.where(NightWorkPlan.status == status.value)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_plan_by_id(
        self, plan_id: UUID, user_id: UUID
    ) -> NightWorkPlan | None:
        """Возвращает план по ID, только если он принадлежит пользователю (IDOR-защита)."""
        result = await self._session.execute(
            self._load_plan_query()
            .where(NightWorkPlan.id == plan_id)
            .where(NightWorkPlan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_block_by_id(
        self, block_id: UUID, plan_id: UUID
    ) -> NightWorkBlock | None:
        """Возвращает блок по ID, только если он принадлежит указанному плану."""
        result = await self._session.execute(
            select(NightWorkBlock)
            .where(NightWorkBlock.id == block_id)
            .where(NightWorkBlock.plan_id == plan_id)
            .options(selectinload(NightWorkBlock.steps))
        )
        return result.scalar_one_or_none()

    async def get_step_by_id(
        self, step_id: UUID, block_id: UUID
    ) -> NightWorkStep | None:
        """Возвращает шаг по ID, только если он принадлежит указанному блоку."""
        result = await self._session.execute(
            select(NightWorkStep)
            .where(NightWorkStep.id == step_id)
            .where(NightWorkStep.block_id == block_id)
        )
        return result.scalar_one_or_none()

    async def save(self, plan: NightWorkPlan) -> NightWorkPlan:
        """Сохраняет план и возвращает обновлённое состояние."""
        self._session.add(plan)
        await self._session.commit()
        await self._session.refresh(plan)
        return plan

    async def update(self, plan: NightWorkPlan) -> NightWorkPlan:
        """Коммитит изменения плана."""
        await self._session.commit()
        await self._session.refresh(plan)
        return plan

    async def delete(self, plan: NightWorkPlan) -> None:
        """Удаляет план из БД."""
        await self._session.delete(plan)
        await self._session.commit()

    async def flush(self) -> None:
        """Сбрасывает отложенные операции без коммита."""
        await self._session.flush()
