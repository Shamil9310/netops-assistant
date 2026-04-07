from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journal import ActivityEntry, ActivityStatus, ActivityType

logger = logging.getLogger(__name__)


def _normalize_search_query(query: str | None) -> str | None:
    """Нормализует пользовательскую строку поиска.

    Бизнес-логика:
    - Пустые и пробельные строки считаются отсутствием фильтра.
    - Непустая строка возвращается без внешних пробелов.
    """
    if query is None:
        return None
    normalized_query = query.strip()
    if normalized_query == "":
        return None
    return normalized_query


def _validate_search_arguments(
    date_from: datetime | None,
    date_to: datetime | None,
    limit: int,
    offset: int,
) -> None:
    """Проверяет валидность аргументов поиска.

    Проверки вынесены в отдельную функцию, чтобы:
    - не дублировать правила в нескольких сервисах;
    - явно фиксировать ошибки входа;
    - покрывать их unit-тестами без запуска БД.
    """
    if date_from is not None and date_to is not None and date_from > date_to:
        raise ValueError("date_from не может быть позже date_to")
    if limit <= 0:
        raise ValueError("limit должен быть больше 0")
    if offset < 0:
        raise ValueError("offset не может быть отрицательным")


def _build_activity_search_filters(
    user_id: UUID,
    query: str | None = None,
    activity_type: ActivityType | None = None,
    status: ActivityStatus | None = None,
    external_ref: str | None = None,
    ticket_number: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[ColumnElement[bool]]:
    """Строит список фильтров для поиска активностей.

    Логика построения фильтров централизована в одном месте:
    это снижает риск расхождения условий между поиском и архивом.
    """
    filters: list[ColumnElement[bool]] = [ActivityEntry.user_id == user_id]

    normalized_query = _normalize_search_query(query)
    if normalized_query is not None:
        pattern = f"%{normalized_query}%"
        filters.append(
            or_(
                ActivityEntry.title.ilike(pattern),
                ActivityEntry.description.ilike(pattern),
                ActivityEntry.external_ref.ilike(pattern),
                ActivityEntry.ticket_number.ilike(pattern),
            )
        )

    if activity_type is not None:
        filters.append(ActivityEntry.activity_type == activity_type.value)
    if status is not None:
        filters.append(ActivityEntry.status == status.value)
    if external_ref is not None:
        filters.append(ActivityEntry.external_ref == external_ref)
    if ticket_number is not None:
        filters.append(ActivityEntry.ticket_number == ticket_number)
    if date_from is not None:
        filters.append(ActivityEntry.work_date >= date_from.date())
    if date_to is not None:
        filters.append(ActivityEntry.work_date <= date_to.date())

    return filters


def _build_archive_status_filter() -> ColumnElement[bool]:
    """Возвращает фильтр архивных статусов.

    Архивом считаются записи, завершившие жизненный цикл:
    - CLOSED
    - CANCELLED
    """
    return ActivityEntry.status.in_([
        ActivityStatus.CLOSED.value,
        ActivityStatus.CANCELLED.value,
    ])


async def _execute_paginated_query(
    session: AsyncSession,
    base_statement: Select[tuple[ActivityEntry]],
    limit: int,
    offset: int,
) -> tuple[list[ActivityEntry], int]:
    """Выполняет пагинированный запрос и корректно считает total."""
    count_statement = select(func.count()).select_from(base_statement.order_by(None).subquery())
    count_result = await session.execute(count_statement)
    total = int(count_result.scalar_one())

    data_statement = base_statement.order_by(ActivityEntry.created_at.desc()).offset(offset).limit(limit)
    data_result = await session.execute(data_statement)
    rows = list(data_result.scalars().all())
    return rows, total


async def search_entries(
    session: AsyncSession,
    user_id: UUID,
    query: str | None = None,
    activity_type: ActivityType | None = None,
    status: ActivityStatus | None = None,
    external_ref: str | None = None,
    ticket_number: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[ActivityEntry], int]:
    """Полнотекстовый и структурный поиск по журналу пользователя.

    Поиск по query ищет совпадения в title, description и external_ref
    через ILIKE (case-insensitive) — достаточно для внутреннего инструмента
    без необходимости поднимать FTS-индексы на этом этапе.

    Возвращает кортеж (результаты, total_count) для поддержки пагинации.
    Пользователь видит только свои записи — изоляция по user_id.
    """
    _validate_search_arguments(date_from=date_from, date_to=date_to, limit=limit, offset=offset)
    filters = _build_activity_search_filters(
        user_id=user_id,
        query=query,
        activity_type=activity_type,
        status=status,
        external_ref=external_ref,
        ticket_number=ticket_number,
        date_from=date_from,
        date_to=date_to,
    )
    statement = select(ActivityEntry).where(and_(*filters))
    rows, total = await _execute_paginated_query(session, statement, limit=limit, offset=offset)

    logger.info(
        "Поиск по журналу: user_id=%s, query=%r, total=%d",
        user_id, query, total,
    )
    return rows, total


async def get_archive_entries(
    session: AsyncSession,
    user_id: UUID,
    query: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    activity_type: ActivityType | None = None,
    external_ref: str | None = None,
    ticket_number: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[ActivityEntry], int]:
    """Архивный поиск — закрытые и отменённые записи с расширенными фильтрами.

    Архив отличается от поиска тем, что по умолчанию показывает только
    завершённые записи (CLOSED + CANCELLED) — исторические данные.
    """
    _validate_search_arguments(date_from=date_from, date_to=date_to, limit=limit, offset=offset)
    filters = _build_activity_search_filters(
        user_id=user_id,
        query=query,
        activity_type=activity_type,
        external_ref=external_ref,
        ticket_number=ticket_number,
        date_from=date_from,
        date_to=date_to,
    )
    filters.append(_build_archive_status_filter())

    statement = select(ActivityEntry).where(and_(*filters))
    rows, total = await _execute_paginated_query(session, statement, limit=limit, offset=offset)
    return rows, total
