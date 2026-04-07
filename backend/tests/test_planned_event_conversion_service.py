"""Тесты конвертации planned event в запись журнала."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.services import planned_event as planned_event_service


@dataclass
class _FakeEvent:
    id: object
    user_id: object
    title: str
    description: str | None
    external_ref: str | None
    scheduled_at: datetime
    is_completed: bool
    linked_journal_entry_id: object | None = None


class _FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, value: object) -> None:
        self.added.append(value)

    async def flush(self) -> None:
        for item in self.added:
            if getattr(item, "id", None) is None:
                setattr(item, "id", uuid4())
        return None

    async def commit(self) -> None:
        return None

    async def refresh(self, _value: object) -> None:
        return None

    async def get(self, _model: object, _pk: object) -> object | None:
        return None


@pytest.mark.asyncio
async def test_convert_event_to_activity_entry_happy_path() -> None:
    """Проверяет создание journal entry и связывание с planned event."""
    fake_session = _FakeSession()
    event = _FakeEvent(
        id=uuid4(),
        user_id=uuid4(),
        title="TrueConf созвон",
        description="Обсуждение change window",
        external_ref="SR-100",
        scheduled_at=datetime(2026, 4, 7, 10, 30, tzinfo=UTC),
        is_completed=False,
    )

    entry = await planned_event_service.convert_event_to_activity_entry(fake_session, event)  # type: ignore[arg-type]

    assert entry.title == "TrueConf созвон"
    assert entry.work_date.isoformat() == "2026-04-07"
    assert entry.ticket_number == "SR-100"
    assert event.linked_journal_entry_id is not None
