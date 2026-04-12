"""Тесты чистой логики сервиса ночных работ."""

import pytest

from app.models.night_work import (
    NightWorkBlockStatus,
    NightWorkPlanStatus,
    NightWorkStepStatus,
)
from app.services.night_work import (
    _normalize_participants,
    _validate_transition,
    _PLAN_ALLOWED_TRANSITIONS,
    _BLOCK_ALLOWED_TRANSITIONS,
    _STEP_ALLOWED_TRANSITIONS,
    render_template_text,
)


class TestNormalizeParticipants:
    def test_empty_list(self):
        assert _normalize_participants([]) == []

    def test_none(self):
        assert _normalize_participants(None) == []

    def test_strips_whitespace(self):
        assert _normalize_participants(["  Иван  ", "  Пётр"]) == ["Иван", "Пётр"]

    def test_removes_duplicates_case_insensitive(self):
        result = _normalize_participants(["Иван", "иван", "ИВАН"])
        assert result == ["Иван"]

    def test_removes_empty_strings(self):
        result = _normalize_participants(["", "   ", "Иван"])
        assert result == ["Иван"]

    def test_preserves_original_case_of_first_occurrence(self):
        result = _normalize_participants(["Пётр", "ПЁТР"])
        assert result == ["Пётр"]


class TestValidateTransition:
    def test_same_status_is_ok(self):
        _validate_transition(
            NightWorkPlanStatus.DRAFT,
            NightWorkPlanStatus.DRAFT,
            _PLAN_ALLOWED_TRANSITIONS,
            "плана",
        )

    def test_allowed_transition(self):
        _validate_transition(
            NightWorkPlanStatus.DRAFT,
            NightWorkPlanStatus.APPROVED,
            _PLAN_ALLOWED_TRANSITIONS,
            "плана",
        )

    def test_forbidden_transition(self):
        with pytest.raises(ValueError, match="Недопустимый переход"):
            _validate_transition(
                NightWorkPlanStatus.COMPLETED,
                NightWorkPlanStatus.DRAFT,
                _PLAN_ALLOWED_TRANSITIONS,
                "плана",
            )

    def test_block_allowed_transition(self):
        _validate_transition(
            NightWorkBlockStatus.PENDING,
            NightWorkBlockStatus.IN_PROGRESS,
            _BLOCK_ALLOWED_TRANSITIONS,
            "блока",
        )

    def test_step_forbidden_after_terminal(self):
        with pytest.raises(ValueError):
            _validate_transition(
                NightWorkStepStatus.COMPLETED,
                NightWorkStepStatus.IN_PROGRESS,
                _STEP_ALLOWED_TRANSITIONS,
                "шага",
            )


class TestRenderTemplateText:
    def test_replaces_variable(self):
        result = render_template_text("Hello {{name}}", {"name": "World"})
        assert result == "Hello World"

    def test_multiple_variables(self):
        result = render_template_text(
            "{{device}} / {{ip}}", {"device": "R1", "ip": "10.0.0.1"}
        )
        assert result == "R1 / 10.0.0.1"

    def test_missing_variable_stays(self):
        result = render_template_text("Hello {{unknown}}", {})
        assert result == "Hello {{unknown}}"

    def test_none_text_returns_none(self):
        result = render_template_text(None, {"key": "val"})
        assert result is None

    def test_empty_variables(self):
        result = render_template_text("Static text", {})
        assert result == "Static text"
