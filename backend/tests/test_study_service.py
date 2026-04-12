"""Тесты сервисного слоя модуля учёбы."""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.study import StudyPlanStatus, StudyPlanTrack, StudySessionStatus
from app.schemas.study import (
    StudyPlanCreateRequest,
    StudyChecklistItemCreateRequest,
    StudyTimerActionRequest,
)
from app.services import study as study_service


def test_study_plan_status_values_are_stable() -> None:
    assert StudyPlanStatus.DRAFT.value == "draft"
    assert StudyPlanStatus.ACTIVE.value == "active"
    assert StudyPlanStatus.COMPLETED.value == "completed"
    assert StudyPlanStatus.CANCELLED.value == "cancelled"


def test_study_plan_track_values_are_stable() -> None:
    assert StudyPlanTrack.PYTHON.value == "python"
    assert StudyPlanTrack.NETWORKS.value == "networks"


def test_study_session_status_values_are_stable() -> None:
    assert StudySessionStatus.RUNNING.value == "running"
    assert StudySessionStatus.PAUSED.value == "paused"
    assert StudySessionStatus.STOPPED.value == "stopped"


def test_validate_plan_transition_rejects_invalid_jump() -> None:
    with pytest.raises(ValueError, match="Недопустимый переход"):
        study_service._validate_plan_transition(
            StudyPlanStatus.DRAFT,
            StudyPlanStatus.COMPLETED,
        )


def test_validate_plan_transition_allows_idempotent_status() -> None:
    study_service._validate_plan_transition(
        StudyPlanStatus.ACTIVE,
        StudyPlanStatus.ACTIVE,
    )


def test_session_duration_seconds_uses_current_time_when_open() -> None:
    started_at = datetime(2026, 4, 7, 9, 0, tzinfo=UTC)
    session = SimpleNamespace(started_at=started_at, ended_at=None)
    current_now = datetime(2026, 4, 7, 9, 45, tzinfo=UTC)

    assert study_service._session_duration_seconds(session, current_now) == 2700


@pytest.mark.asyncio
async def test_create_plan_uses_selected_track(monkeypatch) -> None:
    user = SimpleNamespace(id=uuid4())
    payload = StudyPlanCreateRequest(
        title="Python plan",
        track=StudyPlanTrack.NETWORKS,
    )
    plan = SimpleNamespace(id=uuid4())
    created_plans: list[object] = []

    class FakeSession:
        def add(self, entry) -> None:  # noqa: ANN001
            created_plans.append(entry)

        async def commit(self) -> None:
            return None

    async def fake_refresh_plan(*args: object, **kwargs: object):
        return plan

    monkeypatch.setattr(study_service, "_refresh_plan", fake_refresh_plan)

    result = await study_service.create_plan(FakeSession(), user, payload)

    assert result is plan
    assert len(created_plans) == 1
    assert created_plans[0].track == StudyPlanTrack.NETWORKS.value


@pytest.mark.asyncio
async def test_create_checklist_item_rejects_foreign_checkpoint() -> None:
    plan = SimpleNamespace(id=uuid4())
    request = StudyChecklistItemCreateRequest(
        title="Проверить материал",
        checkpoint_id=uuid4(),
    )
    foreign_checkpoint = SimpleNamespace(plan_id=uuid4())

    class FakeSession:
        async def get(self, model, object_id):  # noqa: ANN001, ARG002
            return foreign_checkpoint

        def add(self, entry) -> None:  # noqa: ANN001
            raise AssertionError("add() should not be called")

        async def commit(self) -> None:
            raise AssertionError("commit() should not be called")

        async def refresh(self, entry) -> None:  # noqa: ANN001, ARG002
            raise AssertionError("refresh() should not be called")

    with pytest.raises(ValueError, match="Чекпоинт не найден"):
        await study_service.create_checklist_item(FakeSession(), plan, request)


@pytest.mark.asyncio
async def test_change_timer_start_creates_running_session(monkeypatch) -> None:
    checkpoint = SimpleNamespace(
        id=uuid4(), plan_id=uuid4(), is_done=False, progress_percent=20
    )
    plan = SimpleNamespace(id=checkpoint.plan_id, status=StudyPlanStatus.DRAFT.value)
    user = SimpleNamespace(id=uuid4())
    payload = StudyTimerActionRequest(action="start", checkpoint_id=checkpoint.id)
    current_now = datetime(2026, 4, 7, 10, 15, tzinfo=UTC)

    created_sessions: list[object] = []

    class FakeSession:
        def add(self, entry) -> None:  # noqa: ANN001
            created_sessions.append(entry)

        async def commit(self) -> None:
            return None

    async def fake_get_active_session_for_user(*args: object, **kwargs: object):
        return None

    async def fake_get_checkpoint_by_id(*args: object, **kwargs: object):
        return checkpoint

    async def fake_refresh_plan(*args: object, **kwargs: object):
        return plan

    monkeypatch.setattr(
        study_service, "get_active_session_for_user", fake_get_active_session_for_user
    )
    monkeypatch.setattr(
        study_service, "get_checkpoint_by_id", fake_get_checkpoint_by_id
    )
    monkeypatch.setattr(study_service, "_refresh_plan", fake_refresh_plan)

    updated = await study_service.change_timer(
        FakeSession(),
        plan,
        user,
        payload,
        now=current_now,
    )

    assert updated is plan
    assert plan.status == StudyPlanStatus.ACTIVE.value
    assert len(created_sessions) == 1
    assert created_sessions[0].plan_id == plan.id
    assert created_sessions[0].checkpoint_id == checkpoint.id
    assert created_sessions[0].status == StudySessionStatus.RUNNING.value
    assert created_sessions[0].started_at == current_now
    assert created_sessions[0].progress_percent == 0


@pytest.mark.asyncio
async def test_change_timer_pause_marks_active_session_finished(monkeypatch) -> None:
    checkpoint = SimpleNamespace(
        id=uuid4(),
        plan_id=uuid4(),
        is_done=False,
        progress_percent=20,
    )
    plan = SimpleNamespace(id=checkpoint.plan_id, status=StudyPlanStatus.ACTIVE.value)
    user = SimpleNamespace(id=uuid4())
    payload = StudyTimerActionRequest(action="pause")
    current_now = datetime(2026, 4, 7, 11, 0, tzinfo=UTC)
    active_session = SimpleNamespace(
        plan_id=plan.id,
        checkpoint_id=checkpoint.id,
        status=StudySessionStatus.RUNNING.value,
        ended_at=None,
        progress_percent=20,
    )

    class FakeSession:
        async def commit(self) -> None:
            return None

    async def fake_get_active_session_for_plan(*args: object, **kwargs: object):
        return active_session

    async def fake_get_checkpoint_by_id(*args: object, **kwargs: object):
        return checkpoint

    async def fake_refresh_plan(*args: object, **kwargs: object):
        return plan

    monkeypatch.setattr(
        study_service, "get_active_session_for_plan", fake_get_active_session_for_plan
    )
    monkeypatch.setattr(
        study_service, "get_checkpoint_by_id", fake_get_checkpoint_by_id
    )
    monkeypatch.setattr(study_service, "_refresh_plan", fake_refresh_plan)

    updated = await study_service.change_timer(
        FakeSession(),
        plan,
        user,
        payload,
        now=current_now,
    )

    assert updated is plan
    assert active_session.status == StudySessionStatus.PAUSED.value
    assert active_session.ended_at == current_now


@pytest.mark.asyncio
async def test_change_timer_stop_keeps_max_progress_when_lower_value_given(
    monkeypatch,
) -> None:
    """Прогресс не уменьшается: если новый % меньше текущего — берём максимум."""
    checkpoint = SimpleNamespace(
        id=uuid4(),
        plan_id=uuid4(),
        is_done=False,
        progress_percent=60,
        completed_at=None,
    )
    plan = SimpleNamespace(id=checkpoint.plan_id, status=StudyPlanStatus.ACTIVE.value)
    user = SimpleNamespace(id=uuid4())
    payload = StudyTimerActionRequest(action="stop", progress_percent=40)
    current_now = datetime(2026, 4, 7, 11, 30, tzinfo=UTC)
    active_session = SimpleNamespace(
        plan_id=plan.id,
        checkpoint_id=checkpoint.id,
        status=StudySessionStatus.RUNNING.value,
        ended_at=None,
        progress_percent=60,
    )

    class FakeSession:
        async def commit(self) -> None:
            return None

    async def fake_get_active_session_for_plan(*args: object, **kwargs: object):
        return active_session

    async def fake_get_checkpoint_by_id(*args: object, **kwargs: object):
        return checkpoint

    async def fake_refresh_plan(*args: object, **kwargs: object):
        return plan

    monkeypatch.setattr(
        study_service, "get_active_session_for_plan", fake_get_active_session_for_plan
    )
    monkeypatch.setattr(
        study_service, "get_checkpoint_by_id", fake_get_checkpoint_by_id
    )
    monkeypatch.setattr(study_service, "_refresh_plan", fake_refresh_plan)

    updated = await study_service.change_timer(
        FakeSession(),
        plan,
        user,
        payload,
        now=current_now,
    )

    assert updated is plan
    assert active_session.status == StudySessionStatus.STOPPED.value
    assert active_session.ended_at == current_now
    assert active_session.progress_percent == 40
    # Новый % (40) меньше текущего (60) — прогресс остаётся 60, тема не закрыта.
    assert checkpoint.progress_percent == 60
    assert checkpoint.is_done is False


@pytest.mark.asyncio
async def test_change_timer_stop_finishes_checkpoint_at_100_percent(
    monkeypatch,
) -> None:
    """При указании 100% тема закрывается как выполненная."""
    checkpoint = SimpleNamespace(
        id=uuid4(),
        plan_id=uuid4(),
        is_done=False,
        progress_percent=60,
        completed_at=None,
    )
    plan = SimpleNamespace(id=checkpoint.plan_id, status=StudyPlanStatus.ACTIVE.value)
    user = SimpleNamespace(id=uuid4())
    payload = StudyTimerActionRequest(action="stop", progress_percent=100)
    current_now = datetime(2026, 4, 7, 12, 0, tzinfo=UTC)
    active_session = SimpleNamespace(
        plan_id=plan.id,
        checkpoint_id=checkpoint.id,
        status=StudySessionStatus.RUNNING.value,
        ended_at=None,
        progress_percent=0,
    )

    class FakeSession:
        async def commit(self) -> None:
            return None

    async def fake_get_active_session_for_plan(*args: object, **kwargs: object):
        return active_session

    async def fake_get_checkpoint_by_id(*args: object, **kwargs: object):
        return checkpoint

    async def fake_refresh_plan(*args: object, **kwargs: object):
        return plan

    monkeypatch.setattr(
        study_service, "get_active_session_for_plan", fake_get_active_session_for_plan
    )
    monkeypatch.setattr(
        study_service, "get_checkpoint_by_id", fake_get_checkpoint_by_id
    )
    monkeypatch.setattr(study_service, "_refresh_plan", fake_refresh_plan)

    updated = await study_service.change_timer(
        FakeSession(),
        plan,
        user,
        payload,
        now=current_now,
    )

    assert updated is plan
    assert checkpoint.progress_percent == 100
    assert checkpoint.is_done is True
    assert checkpoint.completed_at == current_now
    assert checkpoint.completed_at == current_now


@pytest.mark.asyncio
async def test_build_weekly_summary_aggregates_sessions_and_checkpoints(
    monkeypatch,
) -> None:
    week_start = date(2026, 4, 6)
    user = SimpleNamespace(id=uuid4())
    plan_id = uuid4()
    checkpoint = SimpleNamespace(
        id=uuid4(),
        plan_id=plan_id,
        title="Первый модуль",
        progress_percent=100,
        is_done=True,
        completed_at=datetime(2026, 4, 8, 12, 0, tzinfo=UTC),
    )
    sessions = [
        SimpleNamespace(
            id=uuid4(),
            plan_id=plan_id,
            checkpoint_id=checkpoint.id,
            status=StudySessionStatus.STOPPED.value,
            progress_percent=50,
            started_at=datetime(2026, 4, 7, 9, 0, tzinfo=UTC),
            ended_at=datetime(2026, 4, 7, 10, 30, tzinfo=UTC),
            created_at=datetime(2026, 4, 7, 9, 0, tzinfo=UTC),
            updated_at=datetime(2026, 4, 7, 10, 30, tzinfo=UTC),
        ),
        SimpleNamespace(
            id=uuid4(),
            plan_id=plan_id,
            checkpoint_id=checkpoint.id,
            status=StudySessionStatus.STOPPED.value,
            progress_percent=50,
            started_at=datetime(2026, 4, 9, 23, 30, tzinfo=UTC),
            ended_at=datetime(2026, 4, 10, 0, 30, tzinfo=UTC),
            created_at=datetime(2026, 4, 9, 23, 30, tzinfo=UTC),
            updated_at=datetime(2026, 4, 10, 0, 30, tzinfo=UTC),
        ),
    ]
    plan = SimpleNamespace(
        id=plan_id,
        title="Python",
        sessions=sessions,
        checkpoints=[checkpoint],
        checklist_items=[],
    )

    async def fake_list_plans(*args: object, **kwargs: object):
        return [plan]

    monkeypatch.setattr(study_service, "list_plans", fake_list_plans)

    summary = await study_service.build_weekly_summary(
        session=object(),  # type: ignore[arg-type]
        user=user,
        week_start=week_start,
        now=datetime(2026, 4, 10, 12, 0, tzinfo=UTC),
    )

    assert summary.week_start == week_start
    assert summary.total_seconds == 9000
    assert summary.days[1].total_seconds == 5400
    assert summary.days[3].total_seconds == 1800
    assert summary.days[4].total_seconds == 1800
    assert summary.plans[0].title == "Python"
    assert summary.plans[0].total_seconds == 9000
    assert summary.sessions[0].plan_id == str(plan_id)
    assert summary.completed_checkpoints[0].title == "Первый модуль"
