from __future__ import annotations

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.services import schema_guard
from app.services.schema_guard import (
    SchemaVersionMismatchError,
    ensure_schema_is_current,
)


@pytest.mark.asyncio
async def test_ensure_schema_is_current_allows_matching_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Совпадение ревизий означает, что backend может безопасно стартовать."""

    class FakeSession:
        """Заглушка сессии не нужна логике, когда ревизия подменена monkeypatch."""

    async def fake_get_applied_schema_revision(_session: FakeSession) -> str:
        return "0019"

    monkeypatch.setattr(
        schema_guard,
        "get_expected_schema_revision",
        lambda: "0019",
    )
    monkeypatch.setattr(
        schema_guard,
        "get_applied_schema_revision",
        fake_get_applied_schema_revision,
    )

    await ensure_schema_is_current(FakeSession())


@pytest.mark.asyncio
async def test_ensure_schema_is_current_rejects_outdated_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Если БД отстаёт по ревизии, запуск backend должен быть заблокирован."""

    class FakeSession:
        """Заглушка сессии для изолированной проверки бизнес-правила."""

    async def fake_get_applied_schema_revision(_session: FakeSession) -> str:
        return "0018"

    monkeypatch.setattr(
        schema_guard,
        "get_expected_schema_revision",
        lambda: "0019",
    )
    monkeypatch.setattr(
        schema_guard,
        "get_applied_schema_revision",
        fake_get_applied_schema_revision,
    )

    with pytest.raises(SchemaVersionMismatchError, match="ожидается ревизия `0019`"):
        await ensure_schema_is_current(FakeSession())


@pytest.mark.asyncio
async def test_ensure_schema_is_current_explains_missing_alembic_version_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ошибка чтения ревизии должна направлять разработчика к миграциям, а не к догадкам."""

    class FakeSession:
        """Заглушка сессии для воспроизведения ошибки инфраструктуры."""

    async def fake_get_applied_schema_revision(_session: FakeSession) -> str | None:
        raise SQLAlchemyError("relation alembic_version does not exist")

    monkeypatch.setattr(
        schema_guard,
        "get_expected_schema_revision",
        lambda: "0019",
    )
    monkeypatch.setattr(
        schema_guard,
        "get_applied_schema_revision",
        fake_get_applied_schema_revision,
    )

    with pytest.raises(SchemaVersionMismatchError, match="alembic upgrade head"):
        await ensure_schema_is_current(FakeSession())
