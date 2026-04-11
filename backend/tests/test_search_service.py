"""Тесты сервисного слоя поиска и архива."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.models.journal import ActivityStatus, ActivityType
from app.services.search import (
    _build_activity_search_filters,
    _build_archive_status_filter,
    _normalize_search_query,
    _validate_search_arguments,
)


def test_normalize_search_query_trims_value_happy_path() -> None:
    """Проверяет, что строка поиска нормализуется и сохраняет смысловой текст."""
    assert _normalize_search_query("  bgp down  ") == "bgp down"


def test_normalize_search_query_returns_none_for_blank_input() -> None:
    """Проверяет, что пустой и пробельный ввод не считается фильтром."""
    assert _normalize_search_query("") is None
    assert _normalize_search_query("   ") is None
    assert _normalize_search_query(None) is None


def test_validate_search_arguments_rejects_invalid_date_range() -> None:
    """Проверяет ошибку валидации при перевёрнутом диапазоне дат."""
    with pytest.raises(ValueError, match="date_from"):
        _validate_search_arguments(
            date_from=datetime(2026, 4, 8, tzinfo=UTC),
            date_to=datetime(2026, 4, 7, tzinfo=UTC),
            limit=50,
            offset=0,
        )


def test_validate_search_arguments_rejects_invalid_pagination() -> None:
    """Проверяет обработку некорректных limit/offset."""
    with pytest.raises(ValueError, match="limit"):
        _validate_search_arguments(
            date_from=None,
            date_to=None,
            limit=0,
            offset=0,
        )

    with pytest.raises(ValueError, match="offset"):
        _validate_search_arguments(
            date_from=None,
            date_to=None,
            limit=10,
            offset=-1,
        )


def test_build_activity_search_filters_contains_expected_predicates() -> None:
    """Проверяет, что структурные фильтры и полнотекстовый фильтр добавляются вместе."""
    filters = _build_activity_search_filters(
        user_id=uuid4(),
        query="SR1168",
        activity_type=ActivityType.TICKET,
        status=ActivityStatus.CLOSED,
        external_ref="SR11683266",
        service="TrueConf",
        ticket_number="SR11683266",
        date_from=datetime(2026, 4, 1, tzinfo=UTC),
        date_to=datetime(2026, 4, 7, tzinfo=UTC),
    )

    # Один фильтр на пользователя и ещё восемь фильтров по параметрам поиска.
    assert len(filters) == 9


def test_build_activity_search_filters_skips_blank_query() -> None:
    """Проверяет, что пустой query не добавляет полнотекстовый предикат."""
    filters = _build_activity_search_filters(
        user_id=uuid4(),
        query="   ",
    )
    assert len(filters) == 1


def test_build_archive_status_filter_targets_closed_and_cancelled() -> None:
    """Проверяет бизнес-правило архива: только закрытые/отменённые записи."""
    expression = _build_archive_status_filter()
    sql_text = str(
        expression.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )

    assert ActivityStatus.CLOSED.value in sql_text
    assert ActivityStatus.CANCELLED.value in sql_text
