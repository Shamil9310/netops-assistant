"""Тесты для сервисного слоя журнала.

Здесь проверяем только бизнес-логику.
Настоящая база данных не используется: вместо неё подставляем простые заглушки.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.journal import ActivityStatus, ActivityType
from app.schemas.journal import ActivityEntryCreateRequest, ActivityEntryUpdateRequest
from app.services.journal import (
    create_activity_entry,
    delete_activity_entries_for_date,
    delete_all_activity_entries,
    delete_duplicate_activity_entries_for_date,
    delete_selected_activity_entries,
    update_activity_entry,
)

# ---------------------------------------------------------------------------
# Типы активности
# ---------------------------------------------------------------------------


def test_activity_type_values_are_stable() -> None:
    """Значения типов активности не должны меняться — хранятся в БД."""
    assert ActivityType.CALL.value == "call"
    assert ActivityType.TICKET.value == "ticket"
    assert ActivityType.MEETING.value == "meeting"
    assert ActivityType.TASK.value == "task"
    assert ActivityType.ESCALATION.value == "escalation"
    assert ActivityType.OTHER.value == "other"


def test_all_activity_types_are_unique() -> None:
    """Все типы активности должны иметь уникальные строковые значения."""
    values = [t.value for t in ActivityType]
    assert len(values) == len(set(values))


def test_activity_type_count() -> None:
    """Количество типов активности должно соответствовать ожиданиям."""
    assert len(list(ActivityType)) == 6


# ---------------------------------------------------------------------------
# Статусы активности
# ---------------------------------------------------------------------------


def test_activity_status_values_are_stable() -> None:
    """Значения статусов не должны меняться — хранятся в БД."""
    assert ActivityStatus.OPEN.value == "open"
    assert ActivityStatus.IN_PROGRESS.value == "in_progress"
    assert ActivityStatus.CLOSED.value == "closed"
    assert ActivityStatus.CANCELLED.value == "cancelled"


def test_all_statuses_are_unique() -> None:
    """Все статусы должны иметь уникальные строковые значения."""
    values = [s.value for s in ActivityStatus]
    assert len(values) == len(set(values))


def test_activity_status_count() -> None:
    """Количество статусов должно соответствовать ожиданиям."""
    assert len(list(ActivityStatus)) == 4


def test_invalid_activity_type_not_in_enum() -> None:
    """Некорректный тип активности не входит в перечисление."""
    valid_types = {t.value for t in ActivityType}
    assert "phone" not in valid_types
    assert "email" not in valid_types
    assert "" not in valid_types


def test_invalid_status_not_in_enum() -> None:
    """Некорректный статус не входит в перечисление."""
    valid_statuses = {s.value for s in ActivityStatus}
    assert "pending" not in valid_statuses
    assert "done" not in valid_statuses
    assert "" not in valid_statuses


@pytest.mark.asyncio
async def test_create_activity_entry_uses_previous_ended_at_as_started_at() -> None:
    """Если started_at не передан, берём ended_at предыдущей записи за ту же дату."""
    previous_finished_at = datetime(2026, 4, 7, 12, 45, tzinfo=UTC)
    execute_result = SimpleNamespace(scalar_one_or_none=lambda: previous_finished_at)

    class FakeSession:
        def __init__(self) -> None:
            self.added = None

        async def execute(self, statement):
            return execute_result

        def add(self, entry) -> None:
            self.added = entry

        async def commit(self) -> None:
            return None

        async def refresh(self, entry) -> None:
            return None

    session = FakeSession()

    payload = ActivityEntryCreateRequest(
        work_date=date(2026, 4, 7),
        activity_type="task",
        status="open",
        title="Новая задача",
        service="TrueConf",
        started_at=None,
        ended_at=None,
    )
    user = SimpleNamespace(id=uuid4())

    created = await create_activity_entry(session=session, user=user, payload=payload)

    assert created.started_at == datetime(2026, 4, 7, 12, 45, tzinfo=UTC)
    assert created.finished_at is None
    assert created.service == "TrueConf"


@pytest.mark.asyncio
async def test_create_activity_entry_uses_explicit_next_day_for_finished_at() -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.added = None

        async def execute(self, statement):
            return SimpleNamespace(scalar_one_or_none=lambda: None)

        def add(self, entry) -> None:
            self.added = entry

        async def commit(self) -> None:
            return None

        async def refresh(self, entry) -> None:
            return None

    session = FakeSession()

    payload = ActivityEntryCreateRequest(
        work_date=date(2026, 4, 7),
        activity_type="ticket",
        status="open",
        title="Ночная заявка",
        started_at=time(23, 40),
        ended_at=time(1, 10),
        ended_date=date(2026, 4, 8),
    )
    user = SimpleNamespace(id=uuid4())

    created = await create_activity_entry(session=session, user=user, payload=payload)

    assert created.started_at == datetime(2026, 4, 7, 23, 40, tzinfo=UTC)
    assert created.finished_at == datetime(2026, 4, 8, 1, 10, tzinfo=UTC)


@pytest.mark.asyncio
async def test_create_activity_entry_rejects_auto_started_negative_duration() -> None:
    """Автоподстановка started_at не должна обходить проверку конечного времени."""

    previous_finished_at = datetime(2026, 4, 7, 18, 0, tzinfo=UTC)
    execute_result = SimpleNamespace(scalar_one_or_none=lambda: previous_finished_at)

    class FakeSession:
        def __init__(self) -> None:
            self.added = None

        async def execute(self, statement):
            return execute_result

        def add(self, entry) -> None:
            self.added = entry

        async def commit(self) -> None:
            return None

        async def refresh(self, entry) -> None:
            return None

    session = FakeSession()

    payload = ActivityEntryCreateRequest(
        work_date=date(2026, 4, 7),
        activity_type="task",
        status="open",
        title="Новая задача",
        started_at=None,
        ended_at=time(17, 0),
    )
    user = SimpleNamespace(id=uuid4())

    with pytest.raises(ValueError, match="окончания"):
        await create_activity_entry(session=session, user=user, payload=payload)


@pytest.mark.asyncio
async def test_update_activity_entry_clears_nullable_fields() -> None:
    """PATCH с явным null должен очищать nullable-поля записи."""

    class FakeSession:
        def __init__(self) -> None:
            self.committed = False

        async def commit(self) -> None:
            self.committed = True

        async def refresh(self, entry) -> None:
            return None

    entry = SimpleNamespace(
        work_date=date(2026, 4, 7),
        activity_type="task",
        status="open",
        title="Задача",
        description="Описание",
        resolution="Решение",
        contact="Контакт",
        service="Service",
        ticket_number="SR100",
        external_ref="SR100",
        task_url="https://example.test",
        started_at=datetime(2026, 4, 7, 9, 0, tzinfo=UTC),
        finished_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
    )
    payload = ActivityEntryUpdateRequest(
        description=None,
        resolution=None,
        contact=None,
        task_url=None,
        started_at=None,
        ended_at=None,
    )

    updated = await update_activity_entry(
        session=FakeSession(), entry=entry, payload=payload
    )

    assert updated.description is None
    assert updated.resolution is None
    assert updated.contact is None
    assert updated.task_url is None
    assert updated.started_at is None
    assert updated.finished_at is None


@pytest.mark.asyncio
async def test_update_activity_entry_moves_times_with_work_date_change() -> None:
    """Смена work_date должна синхронно переносить связанные временные поля."""

    class FakeSession:
        def __init__(self) -> None:
            self.committed = False

        async def commit(self) -> None:
            self.committed = True

        async def refresh(self, entry) -> None:
            return None

    entry = SimpleNamespace(
        work_date=date(2026, 4, 7),
        activity_type="task",
        status="closed",
        title="Задача",
        description=None,
        resolution=None,
        contact=None,
        service=None,
        ticket_number=None,
        external_ref=None,
        task_url=None,
        started_at=datetime(2026, 4, 7, 9, 15, tzinfo=UTC),
        finished_at=datetime(2026, 4, 7, 10, 45, tzinfo=UTC),
    )
    payload = ActivityEntryUpdateRequest(work_date=date(2026, 4, 8))

    updated = await update_activity_entry(
        session=FakeSession(), entry=entry, payload=payload
    )

    assert updated.work_date == date(2026, 4, 8)
    assert updated.started_at == datetime(2026, 4, 8, 9, 15, tzinfo=UTC)
    assert updated.finished_at == datetime(2026, 4, 8, 10, 45, tzinfo=UTC)


@pytest.mark.asyncio
async def test_delete_duplicate_activity_entries_for_date_keeps_first_ticket_entry() -> (
    None
):
    """При дедупликации сохраняем самую раннюю запись, остальные удаляем."""

    class FakeScalars:
        def __init__(self, entries) -> None:
            self._entries = entries

        def all(self):
            return self._entries

    class FakeResult:
        def __init__(self, entries) -> None:
            self._entries = entries

        def scalars(self) -> FakeScalars:
            return FakeScalars(self._entries)

    class FakeSession:
        def __init__(self, entries) -> None:
            self.entries = entries
            self.deleted_entries = []
            self.commit_called = False

        async def execute(self, _statement):
            return FakeResult(self.entries)

        async def delete(self, entry) -> None:
            self.deleted_entries.append(entry)

        async def commit(self) -> None:
            self.commit_called = True

    first_entry = SimpleNamespace(ticket_number="SR100", id="1")
    duplicate_entry = SimpleNamespace(ticket_number="SR100", id="2")
    unique_entry = SimpleNamespace(ticket_number="SR200", id="3")
    session = FakeSession([first_entry, duplicate_entry, unique_entry])

    removed_count, duplicate_ticket_numbers = (
        await delete_duplicate_activity_entries_for_date(
            session=session,
            user_id=str(uuid4()),
            work_date=date(2026, 4, 10),
        )
    )

    assert removed_count == 1
    assert duplicate_ticket_numbers == ["SR100"]
    assert session.deleted_entries == [duplicate_entry]
    assert session.commit_called is True


@pytest.mark.asyncio
async def test_delete_duplicate_activity_entries_for_date_ignores_entries_without_ticket() -> (
    None
):
    """Ручные записи без номера заявки не считаем дублями Excel-импорта."""

    class FakeScalars:
        def __init__(self, entries) -> None:
            self._entries = entries

        def all(self):
            return self._entries

    class FakeResult:
        def __init__(self, entries) -> None:
            self._entries = entries

        def scalars(self) -> FakeScalars:
            return FakeScalars(self._entries)

    class FakeSession:
        def __init__(self, entries) -> None:
            self.entries = entries
            self.deleted_entries = []
            self.commit_called = False

        async def execute(self, _statement):
            return FakeResult(self.entries)

        async def delete(self, entry) -> None:
            self.deleted_entries.append(entry)

        async def commit(self) -> None:
            self.commit_called = True

    session = FakeSession(
        [
            SimpleNamespace(ticket_number=None, id="1"),
            SimpleNamespace(ticket_number="", id="2"),
        ]
    )

    removed_count, duplicate_ticket_numbers = (
        await delete_duplicate_activity_entries_for_date(
            session=session,
            user_id=str(uuid4()),
            work_date=date(2026, 4, 10),
        )
    )

    assert removed_count == 0
    assert duplicate_ticket_numbers == []
    assert session.deleted_entries == []
    assert session.commit_called is False


@pytest.mark.asyncio
async def test_delete_activity_entries_for_date_removes_all_entries_of_day() -> None:
    """Удаление по дате должно очистить все записи выбранного рабочего дня."""

    class FakeScalars:
        def __init__(self, entries) -> None:
            self._entries = entries

        def all(self):
            return self._entries

    class FakeResult:
        def __init__(self, entries) -> None:
            self._entries = entries

        def scalars(self) -> FakeScalars:
            return FakeScalars(self._entries)

    class FakeSession:
        def __init__(self, entries) -> None:
            self.entries = entries
            self.deleted_entries = []
            self.commit_called = False

        async def execute(self, _statement):
            return FakeResult(self.entries)

        async def delete(self, entry) -> None:
            self.deleted_entries.append(entry)

        async def commit(self) -> None:
            self.commit_called = True

    first_entry = SimpleNamespace(id="1", title="Запись 1")
    second_entry = SimpleNamespace(id="2", title="Запись 2")
    session = FakeSession([first_entry, second_entry])

    removed_count = await delete_activity_entries_for_date(
        session=session,
        user_id=str(uuid4()),
        work_date=date(2026, 4, 10),
    )

    assert removed_count == 2
    assert session.deleted_entries == [first_entry, second_entry]
    assert session.commit_called is True


@pytest.mark.asyncio
async def test_delete_all_activity_entries_removes_everything_for_user() -> None:
    """Полная очистка журнала должна удалять все записи текущего пользователя."""

    class FakeScalars:
        def __init__(self, entries) -> None:
            self._entries = entries

        def all(self):
            return self._entries

    class FakeResult:
        def __init__(self, entries) -> None:
            self._entries = entries

        def scalars(self) -> FakeScalars:
            return FakeScalars(self._entries)

    class FakeSession:
        def __init__(self, entries) -> None:
            self.entries = entries
            self.deleted_entries = []
            self.commit_called = False

        async def execute(self, _statement):
            return FakeResult(self.entries)

        async def delete(self, entry) -> None:
            self.deleted_entries.append(entry)

        async def commit(self) -> None:
            self.commit_called = True

    entries = [
        SimpleNamespace(id="1", title="Запись 1"),
        SimpleNamespace(id="2", title="Запись 2"),
        SimpleNamespace(id="3", title="Запись 3"),
    ]
    session = FakeSession(entries)

    removed_count = await delete_all_activity_entries(
        session=session,
        user_id=str(uuid4()),
    )

    assert removed_count == 3
    assert session.deleted_entries == entries
    assert session.commit_called is True


@pytest.mark.asyncio
async def test_delete_selected_activity_entries_removes_only_requested_ids() -> None:
    """Выборочное удаление должно затрагивать только отмеченные записи пользователя."""

    class FakeScalars:
        def __init__(self, entries) -> None:
            self._entries = entries

        def all(self):
            return self._entries

    class FakeResult:
        def __init__(self, entries) -> None:
            self._entries = entries

        def scalars(self) -> FakeScalars:
            return FakeScalars(self._entries)

    class FakeSession:
        def __init__(self, entries) -> None:
            self.entries = entries
            self.deleted_entries = []
            self.commit_called = False

        async def execute(self, _statement):
            return FakeResult(self.entries)

        async def delete(self, entry) -> None:
            self.deleted_entries.append(entry)

        async def commit(self) -> None:
            self.commit_called = True

    selected_first = SimpleNamespace(id="1", title="Первая")
    selected_second = SimpleNamespace(id="2", title="Вторая")
    session = FakeSession([selected_first, selected_second])

    removed_count = await delete_selected_activity_entries(
        session=session,
        user_id=str(uuid4()),
        entry_ids=["1", "2", "999"],
    )

    assert removed_count == 2
    assert session.deleted_entries == [selected_first, selected_second]
    assert session.commit_called is True
