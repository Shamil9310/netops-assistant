"""Тесты сервисного слоя Work Timer."""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_timer import WorkTimerSessionStatus, WorkTimerTaskStatus
from app.schemas.work_timer import (
    WorkTimerTaskCreateRequest,
    WorkTimerTimerActionRequest,
)
from app.services import work_timer as work_timer_service


def test_work_timer_status_values_are_stable() -> None:
    assert WorkTimerTaskStatus.TODO.value == "todo"
    assert WorkTimerTaskStatus.IN_PROGRESS.value == "in_progress"
    assert WorkTimerTaskStatus.DONE.value == "done"
    assert WorkTimerTaskStatus.CANCELLED.value == "cancelled"
    assert WorkTimerSessionStatus.RUNNING.value == "running"
    assert WorkTimerSessionStatus.PAUSED.value == "paused"
    assert WorkTimerSessionStatus.STOPPED.value == "stopped"


def test_normalize_tags_deduplicates_and_trims() -> None:
    assert work_timer_service._normalize_tags(["  api  ", "ops", "api", ""]) == [
        "api",
        "ops",
    ]


@pytest.mark.asyncio
async def test_create_task_normalizes_text_and_tags(monkeypatch) -> None:
    user = SimpleNamespace(id=uuid4())
    payload = WorkTimerTaskCreateRequest(
        title="  Fix VPN issue  ",
        description="  разбор инцидента  ",
        task_ref="  INC-1  ",
        task_url="  https://example.com/task  ",
        tags=[" ops ", "ops", "network "],
        order_index=2,
        status=WorkTimerTaskStatus.TODO,
    )
    task = SimpleNamespace(
        id=uuid4(),
        user_id=user.id,
        title="Fix VPN issue",
        description="разбор инцидента",
        task_ref="INC-1",
        task_url="https://example.com/task",
        tags=["ops", "network"],
        order_index=2,
        status=WorkTimerTaskStatus.TODO.value,
        completed_at=None,
        sessions=[],
        created_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
        updated_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
    )

    async def fake_save_task(self, created_task):  # noqa: ANN001
        return task

    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository, "save_task", fake_save_task
    )

    result = await work_timer_service.create_task(SimpleNamespace(), user, payload)

    assert result.title == "Fix VPN issue"
    assert result.tags == ["ops", "network"]
    assert result.task_ref == "INC-1"


@pytest.mark.asyncio
async def test_start_pause_resume_stop_timer(monkeypatch) -> None:
    user = SimpleNamespace(id=uuid4())
    task = SimpleNamespace(
        id=uuid4(),
        user_id=user.id,
        title="Patch switch",
        description=None,
        task_ref="SR-1",
        task_url=None,
        tags=["ops", "network"],
        order_index=0,
        status=WorkTimerTaskStatus.TODO.value,
        completed_at=None,
        sessions=[],
        created_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
        updated_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
    )
    now_start = datetime(2026, 4, 12, 10, 0, tzinfo=UTC)
    now_pause = datetime(2026, 4, 12, 10, 15, tzinfo=UTC)
    now_resume = datetime(2026, 4, 12, 10, 25, tzinfo=UTC)
    now_stop = datetime(2026, 4, 12, 10, 45, tzinfo=UTC)
    created_session = None

    def make_session(**kwargs):  # noqa: ANN001
        now = kwargs.get("started_at", datetime(2026, 4, 12, 10, 0, tzinfo=UTC))
        return SimpleNamespace(
            id=uuid4(),
            ended_at=None,
            created_at=now,
            updated_at=now,
            interruptions=[],
            **kwargs,
        )

    def make_interruption(**kwargs):  # noqa: ANN001
        now = kwargs.get("started_at", datetime(2026, 4, 12, 10, 0, tzinfo=UTC))
        return SimpleNamespace(
            id=uuid4(),
            ended_at=None,
            created_at=now,
            updated_at=now,
            **kwargs,
        )

    class FakeDB:
        def add(self, instance) -> None:  # noqa: ANN001
            nonlocal created_session
            if getattr(instance, "task_id", None) == task.id:
                created_session = instance
                task.sessions.append(instance)
            if (
                created_session is not None
                and getattr(instance, "session_id", None) == created_session.id
            ):
                created_session.interruptions.append(instance)

        async def commit(self) -> None:
            return None

        async def refresh(self, instance) -> None:  # noqa: ANN001
            return None

    async def fake_get_active_session_for_user(self, user_id):  # noqa: ANN001
        return next(
            (session for session in task.sessions if session.ended_at is None), None
        )

    async def fake_get_active_session_for_task(self, task_id):  # noqa: ANN001
        if task_id != task.id:
            return None
        return next(
            (session for session in task.sessions if session.ended_at is None), None
        )

    async def fake_get_task_by_id(self, user_id, task_id):  # noqa: ANN001
        return task if task_id == task.id and user_id == user.id else None

    async def fake_update_task(self, task_model):  # noqa: ANN001
        return task_model

    async def fake_update_session(self, session_model):  # noqa: ANN001
        return session_model

    async def fake_update_interruption(self, interruption_model):  # noqa: ANN001
        return interruption_model

    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository,
        "get_active_session_for_user",
        fake_get_active_session_for_user,
    )
    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository,
        "get_active_session_for_task",
        fake_get_active_session_for_task,
    )
    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository, "get_task_by_id", fake_get_task_by_id
    )
    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository, "update_task", fake_update_task
    )
    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository, "update_session", fake_update_session
    )
    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository,
        "update_interruption",
        fake_update_interruption,
    )
    monkeypatch.setattr(work_timer_service, "WorkTimerSession", make_session)
    monkeypatch.setattr(work_timer_service, "WorkTimerInterruption", make_interruption)

    started = await work_timer_service.change_timer(
        FakeDB(),
        task,
        user,
        WorkTimerTimerActionRequest(action="start"),
        now=now_start,
    )
    assert started.active_session_id is not None
    assert task.status == WorkTimerTaskStatus.IN_PROGRESS.value
    assert len(task.sessions) == 1
    assert task.sessions[0].status == WorkTimerSessionStatus.RUNNING.value
    assert task.sessions[0].tags_snapshot == ["ops", "network"]

    paused = await work_timer_service.change_timer(
        FakeDB(),
        task,
        user,
        WorkTimerTimerActionRequest(action="pause", interruption_reason="Звонок"),
        now=now_pause,
    )
    assert paused.sessions[0].status == WorkTimerSessionStatus.PAUSED.value
    assert len(paused.sessions[0].interruptions) == 1
    assert paused.sessions[0].interruptions[0].ended_at is None

    resumed = await work_timer_service.change_timer(
        FakeDB(),
        task,
        user,
        WorkTimerTimerActionRequest(action="resume"),
        now=now_resume,
    )
    assert resumed.sessions[0].status == WorkTimerSessionStatus.RUNNING.value
    assert resumed.sessions[0].interruptions[0].ended_at == now_resume

    stopped = await work_timer_service.change_timer(
        FakeDB(),
        task,
        user,
        WorkTimerTimerActionRequest(action="stop"),
        now=now_stop,
    )
    assert stopped.sessions[0].status == WorkTimerSessionStatus.STOPPED.value
    assert stopped.sessions[0].ended_at == now_stop
    assert stopped.total_seconds == 35 * 60
    assert stopped.interruption_seconds == 10 * 60


@pytest.mark.asyncio
async def test_weekly_summary_aggregates_tasks_tags_and_days(monkeypatch) -> None:
    task = SimpleNamespace(id=uuid4(), title="Deploy router")
    second_task = SimpleNamespace(id=uuid4(), title="Fix ACL")

    interruption = SimpleNamespace(
        id=uuid4(),
        session_id=uuid4(),
        reason="call",
        started_at=datetime(2026, 4, 7, 9, 15, tzinfo=UTC),
        ended_at=datetime(2026, 4, 7, 9, 25, tzinfo=UTC),
        created_at=datetime(2026, 4, 7, 9, 15, tzinfo=UTC),
        updated_at=datetime(2026, 4, 7, 9, 25, tzinfo=UTC),
    )
    session_one = SimpleNamespace(
        id=uuid4(),
        task_id=task.id,
        task=task,
        status=WorkTimerSessionStatus.STOPPED.value,
        tags_snapshot=["network", "ops"],
        started_at=datetime(2026, 4, 7, 9, 0, tzinfo=UTC),
        ended_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
        created_at=datetime(2026, 4, 7, 9, 0, tzinfo=UTC),
        updated_at=datetime(2026, 4, 7, 10, 0, tzinfo=UTC),
        interruptions=[interruption],
    )
    session_two = SimpleNamespace(
        id=uuid4(),
        task_id=second_task.id,
        task=second_task,
        status=WorkTimerSessionStatus.STOPPED.value,
        tags_snapshot=["ops"],
        started_at=datetime(2026, 4, 8, 14, 0, tzinfo=UTC),
        ended_at=datetime(2026, 4, 8, 15, 0, tzinfo=UTC),
        created_at=datetime(2026, 4, 8, 14, 0, tzinfo=UTC),
        updated_at=datetime(2026, 4, 8, 15, 0, tzinfo=UTC),
        interruptions=[],
    )

    async def fake_list_sessions_for_week(
        self, user_id, week_start, week_end
    ):  # noqa: ANN001
        return [session_one, session_two]

    async def fake_list_tasks(self, user_id):  # noqa: ANN001
        return [task, second_task]

    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository,
        "list_sessions_for_week",
        fake_list_sessions_for_week,
    )
    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository, "list_tasks", fake_list_tasks
    )

    summary = await work_timer_service.get_weekly_summary(
        SimpleNamespace(),
        uuid4(),
        date(2026, 4, 6),
    )

    assert summary.total_seconds == 6600
    assert summary.days[1].sessions_count == 1
    assert summary.days[1].interruptions_count == 1
    assert summary.tasks[0].title == "Fix ACL"
    assert summary.tags[0].tag == "ops"
    assert len(summary.sessions) == 2


@pytest.mark.asyncio
async def test_update_and_delete_task_cover_repository_flow(monkeypatch) -> None:
    task = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        title="Old title",
        description=None,
        task_ref=None,
        task_url=None,
        tags=["old"],
        order_index=1,
        status=WorkTimerTaskStatus.TODO.value,
        completed_at=None,
        sessions=[],
        created_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
        updated_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
    )
    payload = work_timer_service.WorkTimerTaskUpdateRequest(
        title="  New title  ",
        description="  Description  ",
        task_ref="  INC-2  ",
        task_url="  https://example.com/inc-2  ",
        tags=["net", "net", "ops"],
        order_index=4,
        status=WorkTimerTaskStatus.DONE,
        completed_at=datetime(2026, 4, 12, 11, 0, tzinfo=UTC),
    )
    calls: list[str] = []

    async def fake_update_task(self, task_model):  # noqa: ANN001
        calls.append("update")
        return task_model

    async def fake_delete_task(self, task_model):  # noqa: ANN001
        calls.append("delete")
        return None

    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository, "update_task", fake_update_task
    )
    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository, "delete_task", fake_delete_task
    )

    updated = await work_timer_service.update_task(SimpleNamespace(), task, payload)
    await work_timer_service.delete_task(SimpleNamespace(), task)

    assert updated.title == "New title"
    assert updated.description == "Description"
    assert updated.task_ref == "INC-2"
    assert updated.task_url == "https://example.com/inc-2"
    assert updated.tags == ["net", "ops"]
    assert updated.order_index == 4
    assert updated.status == WorkTimerTaskStatus.DONE
    assert updated.completed_at == datetime(2026, 4, 12, 11, 0, tzinfo=UTC)
    assert calls == ["update", "delete"]


@pytest.mark.asyncio
async def test_timer_error_branches_raise_helpful_messages(monkeypatch) -> None:
    user = SimpleNamespace(id=uuid4())
    done_task = SimpleNamespace(
        id=uuid4(),
        user_id=user.id,
        title="Finished",
        description=None,
        task_ref=None,
        task_url=None,
        tags=[],
        order_index=0,
        status=WorkTimerTaskStatus.DONE.value,
        completed_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
        sessions=[],
        created_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
        updated_at=datetime(2026, 4, 12, 10, 0, tzinfo=UTC),
    )

    async def fake_get_active_session_for_user(self, user_id):  # noqa: ANN001
        return None

    async def fake_get_active_session_for_task(self, task_id):  # noqa: ANN001
        return None

    async def fake_update_task(self, task_model):  # noqa: ANN001
        return task_model

    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository,
        "get_active_session_for_user",
        fake_get_active_session_for_user,
    )
    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository,
        "get_active_session_for_task",
        fake_get_active_session_for_task,
    )
    monkeypatch.setattr(
        work_timer_service.WorkTimerRepository, "update_task", fake_update_task
    )

    with pytest.raises(ValueError, match="Нельзя запускать таймер"):
        await work_timer_service.change_timer(
            SimpleNamespace(),
            done_task,
            user,
            WorkTimerTimerActionRequest(action="start"),
            now=datetime(2026, 4, 12, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="Сначала запусти таймер"):
        await work_timer_service.change_timer(
            SimpleNamespace(),
            done_task,
            user,
            WorkTimerTimerActionRequest(action="pause"),
            now=datetime(2026, 4, 12, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="Сначала поставь таймер на паузу"):
        await work_timer_service.change_timer(
            SimpleNamespace(),
            done_task,
            user,
            WorkTimerTimerActionRequest(action="resume"),
            now=datetime(2026, 4, 12, 12, 0, tzinfo=UTC),
        )
