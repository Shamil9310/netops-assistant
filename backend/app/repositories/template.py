"""Репозиторий для работы с шаблонами ночных работ."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.template import PlanTemplate
from app.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[PlanTemplate]):
    """Репозиторий шаблонов планов ночных работ."""

    async def list_for_user(
        self,
        user_id: UUID,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> list[PlanTemplate]:
        """Возвращает шаблоны пользователя с необязательной фильтрацией."""
        query = (
            select(PlanTemplate)
            .where(PlanTemplate.user_id == user_id)
            .order_by(PlanTemplate.created_at.desc())
        )
        if category is not None:
            query = query.where(PlanTemplate.category == category)
        if is_active is not None:
            query = query.where(PlanTemplate.is_active == is_active)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        template_id: UUID,
        user_id: UUID,
    ) -> PlanTemplate | None:
        """Возвращает шаблон по ID в пределах библиотеки пользователя."""
        result = await self._session.execute(
            select(PlanTemplate)
            .where(PlanTemplate.id == template_id)
            .where(PlanTemplate.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_key(self, key: str, user_id: UUID) -> PlanTemplate | None:
        """Возвращает шаблон по ключу в пределах библиотеки пользователя."""
        result = await self._session.execute(
            select(PlanTemplate)
            .where(PlanTemplate.key == key)
            .where(PlanTemplate.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def save(self, template: PlanTemplate) -> PlanTemplate:
        """Сохраняет шаблон и возвращает его обновлённое состояние."""
        self._session.add(template)
        await self._session.commit()
        await self._session.refresh(template)
        return template

    async def save_all(self, templates: list[PlanTemplate]) -> list[PlanTemplate]:
        """Сохраняет список шаблонов и возвращает их обновлённое состояние."""
        self._session.add_all(templates)
        await self._session.commit()
        for template in templates:
            await self._session.refresh(template)
        return templates

    async def update(self, template: PlanTemplate) -> PlanTemplate:
        """Коммитит изменения шаблона."""
        await self._session.commit()
        await self._session.refresh(template)
        return template

    async def delete(self, template: PlanTemplate) -> None:
        """Удаляет шаблон из БД."""
        await self._session.delete(template)
        await self._session.commit()
