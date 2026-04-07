"""Тесты генератора отчётов (Sprint 12: Reports engine v1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.models.journal import ActivityStatus, ActivityType
from app.services import reports as reports_service


@dataclass(slots=True)
class _FakeEntry:
    """Тестовая модель записи журнала для проверки генератора отчётов."""

    work_date: date
    activity_type: str
    status: str
    title: str
    description: str | None
    external_ref: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


@dataclass(slots=True)
class _FakeNightWorkStep:
    title: str
    description: str | None
    status: str
    is_rollback: bool
    is_post_action: bool
    actual_result: str | None
    executor_comment: str | None
    collaborators: list[str]
    handoff_to: str | None


@dataclass(slots=True)
class _FakeNightWorkBlock:
    title: str
    sr_number: str | None
    description: str | None
    status: str
    result_comment: str | None
    steps: list[_FakeNightWorkStep]


@dataclass(slots=True)
class _FakeNightWorkPlan:
    title: str
    status: str
    description: str | None
    scheduled_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    blocks: list[_FakeNightWorkBlock]


@pytest.mark.asyncio
async def test_generate_daily_report_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет daily-отчёт на happy path: есть записи и итоговая статистика."""
    entries = [
        _FakeEntry(
            work_date=date(2026, 4, 7),
            activity_type=ActivityType.TICKET.value,
            status=ActivityStatus.CLOSED.value,
            title="Разбор SR11683266",
            description="Проверили BGP соседство и маршруты.",
            external_ref="SR11683266",
            started_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
            finished_at=datetime(2026, 4, 7, 11, 0, tzinfo=UTC),
            created_at=datetime(2026, 4, 7, 11, 5, tzinfo=UTC),
        ),
    ]

    async def _fake_list_entries_for_date(*args: object, **kwargs: object) -> list[_FakeEntry]:
        return entries

    monkeypatch.setattr(reports_service, "list_entries_for_date", _fake_list_entries_for_date)
    report = await reports_service.generate_daily_report(
        session=object(),  # type: ignore[arg-type]
        user_id=uuid4(),
        report_date=date(2026, 4, 7),
        author_name="Шамиль Исаев",
    )

    assert "# Дневной отчёт" in report
    assert "Разбор SR11683266" in report
    assert "SR11683266" in report
    assert "## Итоги" in report
    assert "Всего записей" in report
    assert "Суммарное время" in report


@pytest.mark.asyncio
async def test_generate_daily_report_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет edge-case: если записей нет, отчёт возвращает понятный текст."""
    async def _fake_list_entries_for_date(*args: object, **kwargs: object) -> list[_FakeEntry]:
        return []

    monkeypatch.setattr(reports_service, "list_entries_for_date", _fake_list_entries_for_date)
    report = await reports_service.generate_daily_report(
        session=object(),  # type: ignore[arg-type]
        user_id=uuid4(),
        report_date=date(2026, 4, 7),
        author_name="Шамиль Исаев",
    )

    assert "Записей за день не найдено" in report


@pytest.mark.asyncio
async def test_generate_weekly_report_groups_entries_by_days(monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет weekly-отчёт: записи группируются по дням периода."""
    entries = [
        _FakeEntry(
            work_date=date(2026, 4, 7),
            activity_type=ActivityType.CALL.value,
            status=ActivityStatus.CLOSED.value,
            title="Созвон с командой",
            description=None,
            external_ref=None,
            started_at=datetime(2026, 4, 7, 9, 0, tzinfo=UTC),
            finished_at=datetime(2026, 4, 7, 9, 30, tzinfo=UTC),
            created_at=datetime(2026, 4, 7, 9, 30, tzinfo=UTC),
        ),
        _FakeEntry(
            work_date=date(2026, 4, 8),
            activity_type=ActivityType.TASK.value,
            status=ActivityStatus.IN_PROGRESS.value,
            title="Подготовка плана работ",
            description="Черновик с rollback шагами.",
            external_ref="WA00468580",
            started_at=datetime(2026, 4, 8, 12, 0, tzinfo=UTC),
            finished_at=None,
            created_at=datetime(2026, 4, 8, 12, 30, tzinfo=UTC),
        ),
    ]

    async def _fake_list_entries_for_date(*args: object, **kwargs: object) -> list[_FakeEntry]:
        return entries

    monkeypatch.setattr(reports_service, "list_entries_for_date", _fake_list_entries_for_date)
    report = await reports_service.generate_weekly_report(
        session=object(),  # type: ignore[arg-type]
        user_id=uuid4(),
        week_start=date(2026, 4, 6),
        author_name="Шамиль Исаев",
    )

    assert "# Недельный отчёт" in report
    assert "07.04.2026" in report
    assert "08.04.2026" in report
    assert "Созвон с командой" in report
    assert "Подготовка плана работ" in report


@pytest.mark.asyncio
async def test_generate_range_report_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Проверяет range-отчёт: формируется markdown за произвольный период."""
    entries = [
        _FakeEntry(
            work_date=date(2026, 4, 10),
            activity_type=ActivityType.OTHER.value,
            status=ActivityStatus.CANCELLED.value,
            title="Отменённое обслуживание",
            description="Окно отменено из-за зависимостей.",
            external_ref="SR100500",
            started_at=None,
            finished_at=None,
            created_at=datetime(2026, 4, 10, 18, 0, tzinfo=UTC),
        ),
    ]

    async def _fake_list_entries_for_date(*args: object, **kwargs: object) -> list[_FakeEntry]:
        return entries

    monkeypatch.setattr(reports_service, "list_entries_for_date", _fake_list_entries_for_date)
    report = await reports_service.generate_range_report(
        session=object(),  # type: ignore[arg-type]
        user_id=uuid4(),
        date_from=date(2026, 4, 9),
        date_to=date(2026, 4, 11),
        author_name="Шамиль Исаев",
    )

    assert "# Отчёт за период" in report
    assert "Отменённое обслуживание" in report
    assert "SR100500" in report
    assert "## Итоги" in report


def test_build_night_work_follow_up_summary_happy_path() -> None:
    """Проверяет summary по ночным работам с completed/failed метриками."""
    plan = _FakeNightWorkPlan(
        title="Night window DC3/DC4",
        status="completed",
        description="Описание плана",
        scheduled_at=None,
        started_at=None,
        finished_at=None,
        blocks=[
            _FakeNightWorkBlock(
                title="SR11683266",
                sr_number="SR11683266",
                description=None,
                status="completed",
                result_comment=None,
                steps=[
                    _FakeNightWorkStep(
                        title="Pre-check",
                        description=None,
                        status="completed",
                        is_rollback=False,
                        is_post_action=False,
                        actual_result="OK",
                        executor_comment=None,
                        collaborators=[],
                        handoff_to=None,
                    ),
                    _FakeNightWorkStep(
                        title="Config apply",
                        description=None,
                        status="failed",
                        is_rollback=False,
                        is_post_action=False,
                        actual_result="Ошибка команды",
                        executor_comment="Неверный контекст",
                        collaborators=["oncall-db"],
                        handoff_to="Core Network Team",
                    ),
                ],
            ),
        ],
    )

    summary = reports_service._build_night_work_follow_up_summary(plan)  # noqa: SLF001
    assert "Night window DC3/DC4" in summary
    assert "Не выполнено: 1" in summary
    assert "Выполнено: 1" in summary
    assert "Передано: 1" in summary


def test_build_night_work_report_contains_blocks_steps_and_summary() -> None:
    """Проверяет markdown отчёт по ночным работам: блоки, шаги и follow-up секция."""
    plan = _FakeNightWorkPlan(
        title="Night BGP changes",
        status="in_progress",
        description="План смены соседств",
        scheduled_at=datetime(2026, 4, 7, 22, 0, tzinfo=UTC),
        started_at=datetime(2026, 4, 7, 22, 5, tzinfo=UTC),
        finished_at=None,
        blocks=[
            _FakeNightWorkBlock(
                title="SR11690000",
                sr_number="SR11690000",
                description="Основной блок",
                status="in_progress",
                result_comment="Промежуточно",
                steps=[
                    _FakeNightWorkStep(
                        title="Rollback template",
                        description="Проверка rollback",
                        status="pending",
                        is_rollback=True,
                        is_post_action=False,
                        actual_result=None,
                        executor_comment=None,
                        collaborators=[],
                        handoff_to=None,
                    ),
                ],
            ),
        ],
    )

    report = reports_service._build_night_work_report(plan, "Шамиль Исаев")  # noqa: SLF001
    assert "# Итог ночных работ" in report
    assert "SR11690000" in report
    assert "Rollback template" in report
    assert "rollback" in report
    assert "Morning follow-up summary" in report
