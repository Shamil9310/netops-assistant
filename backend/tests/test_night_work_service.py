"""Тесты бизнес-логики жизненного цикла night work."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.models.night_work import NightWorkBlockStatus, NightWorkPlanStatus, NightWorkStepStatus
from app.services.night_work import (
    _resolve_finished_at,
    _resolve_started_at,
    _validate_transition,
    render_template_text,
)


def test_validate_transition_allows_happy_path_for_plan() -> None:
    """Проверяет валидный переход статуса плана по lifecycle."""
    allowed = {
        NightWorkPlanStatus.DRAFT: {NightWorkPlanStatus.APPROVED},
        NightWorkPlanStatus.APPROVED: {NightWorkPlanStatus.IN_PROGRESS},
        NightWorkPlanStatus.IN_PROGRESS: {NightWorkPlanStatus.COMPLETED},
        NightWorkPlanStatus.COMPLETED: set(),
        NightWorkPlanStatus.CANCELLED: set(),
    }
    _validate_transition(
        current_status=NightWorkPlanStatus.DRAFT,
        next_status=NightWorkPlanStatus.APPROVED,
        allowed=allowed,
        object_name="плана",
    )


def test_validate_transition_rejects_invalid_jump() -> None:
    """Проверяет edge-case: переход через этапы запрещён."""
    allowed = {
        NightWorkPlanStatus.DRAFT: {NightWorkPlanStatus.APPROVED},
        NightWorkPlanStatus.APPROVED: {NightWorkPlanStatus.IN_PROGRESS},
        NightWorkPlanStatus.IN_PROGRESS: {NightWorkPlanStatus.COMPLETED},
        NightWorkPlanStatus.COMPLETED: set(),
        NightWorkPlanStatus.CANCELLED: set(),
    }
    with pytest.raises(ValueError, match="Недопустимый переход"):
        _validate_transition(
            current_status=NightWorkPlanStatus.DRAFT,
            next_status=NightWorkPlanStatus.COMPLETED,
            allowed=allowed,
            object_name="плана",
        )


def test_validate_transition_allows_idempotent_call() -> None:
    """Проверяет, что повторный вызов с тем же статусом допускается."""
    allowed = {
        NightWorkBlockStatus.PENDING: {NightWorkBlockStatus.IN_PROGRESS},
        NightWorkBlockStatus.IN_PROGRESS: {NightWorkBlockStatus.COMPLETED},
        NightWorkBlockStatus.COMPLETED: set(),
        NightWorkBlockStatus.FAILED: set(),
        NightWorkBlockStatus.SKIPPED: set(),
    }
    _validate_transition(
        current_status=NightWorkBlockStatus.PENDING,
        next_status=NightWorkBlockStatus.PENDING,
        allowed=allowed,
        object_name="блока",
    )


def test_resolve_started_at_sets_value_for_in_progress() -> None:
    """Проверяет автопроставление started_at при старте исполнения."""
    started_at = _resolve_started_at(
        current_started_at=None,
        started_at_from_request=None,
        new_status_value=NightWorkStepStatus.IN_PROGRESS.value,
    )
    assert started_at is not None


def test_resolve_started_at_respects_explicit_value() -> None:
    """Проверяет приоритет времени старта из запроса."""
    explicit_value = datetime(2026, 4, 7, 1, 0, tzinfo=UTC)
    started_at = _resolve_started_at(
        current_started_at=None,
        started_at_from_request=explicit_value,
        new_status_value=NightWorkStepStatus.IN_PROGRESS.value,
    )
    assert started_at == explicit_value


def test_resolve_finished_at_sets_value_for_terminal_status() -> None:
    """Проверяет автопроставление finished_at для terminal-статусов."""
    finished_at = _resolve_finished_at(
        current_finished_at=None,
        finished_at_from_request=None,
        new_status_value=NightWorkStepStatus.COMPLETED.value,
    )
    assert finished_at is not None


def test_resolve_finished_at_sets_value_for_blocked_status() -> None:
    """Проверяет, что blocked считается terminal-статусом исполнения."""
    finished_at = _resolve_finished_at(
        current_finished_at=None,
        finished_at_from_request=None,
        new_status_value=NightWorkStepStatus.BLOCKED.value,
    )
    assert finished_at is not None


def test_resolve_finished_at_keeps_none_for_non_terminal_status() -> None:
    """Проверяет, что для промежуточных статусов finished_at не проставляется."""
    finished_at = _resolve_finished_at(
        current_finished_at=None,
        finished_at_from_request=None,
        new_status_value=NightWorkStepStatus.IN_PROGRESS.value,
    )
    assert finished_at is None


def test_render_template_text_happy_path() -> None:
    """Проверяет подстановку переменных в шаблонный текст."""
    rendered = render_template_text(
        "BGP peer {{neighbor_ip}} on {{device}}",
        {"neighbor_ip": "10.10.10.1", "device": "RST-DC4-BGW1"},
    )
    assert rendered == "BGP peer 10.10.10.1 on RST-DC4-BGW1"


def test_render_template_text_edge_cases() -> None:
    """Проверяет edge-cases: None и неизвестные переменные."""
    assert render_template_text(None, {"var": "value"}) is None
    assert render_template_text("SR {{sr}} / {{missing}}", {"sr": "SR11683266"}) == "SR SR11683266 / {{missing}}"
