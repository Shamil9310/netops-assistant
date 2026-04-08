"""Придирчивые тесты API-роутов командной выгрузки отчётов."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes import team as team_routes


def _request_with_id(request_id: str = "req-1") -> SimpleNamespace:
    return SimpleNamespace(state=SimpleNamespace(request_id=request_id))


@pytest.mark.asyncio
async def test_export_daily_report_for_user_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    current_user = SimpleNamespace(id=uuid4())
    team_member = SimpleNamespace(
        id=user_id, username="ivan", full_name="Иван Кузнецов"
    )
    request = _request_with_id("daily-req")

    async def _fake_get_user_by_id(*args: object, **kwargs: object) -> object:
        return team_member

    async def _fake_generate_daily_report(*args: object, **kwargs: object) -> str:
        return "# daily report"

    log_called: dict[str, str] = {}

    async def _fake_log_access_event(*args: object, **kwargs: object) -> None:
        log_called["resource_type"] = str(kwargs.get("resource_type"))

    monkeypatch.setattr(
        team_routes.team_service, "get_user_by_id", _fake_get_user_by_id
    )
    monkeypatch.setattr(
        team_routes.reports_service,
        "generate_daily_report",
        _fake_generate_daily_report,
    )
    monkeypatch.setattr(team_routes, "log_access_event", _fake_log_access_event)

    response = await team_routes.export_daily_report_for_user(
        user_id=user_id,
        current_user=current_user,  # type: ignore[arg-type]
        request=request,  # type: ignore[arg-type]
        report_date=date(2026, 4, 8),
        db=object(),  # type: ignore[arg-type]
    )

    assert response.status_code == 200
    assert response.body == b"# daily report"
    assert (
        'attachment; filename="team_daily_ivan_2026-04-08.md"'
        in response.headers["content-disposition"]
    )
    assert log_called["resource_type"] == "team_daily_report"


@pytest.mark.asyncio
async def test_export_weekly_report_for_team_member_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    current_user = SimpleNamespace(id=uuid4())
    team_member = SimpleNamespace(
        id=user_id, username="anna", full_name="Анна Смирнова"
    )
    request = _request_with_id("weekly-req")

    async def _fake_scope_check(*args: object, **kwargs: object) -> bool:
        raise AssertionError(
            "is_user_in_manager_scope must not be called for global manager access"
        )

    async def _fake_get_user_by_id(*args: object, **kwargs: object) -> object:
        return team_member

    async def _fake_generate_weekly_report(*args: object, **kwargs: object) -> str:
        return "# weekly report"

    async def _fake_log_access_event(*args: object, **kwargs: object) -> None:
        return None

    monkeypatch.setattr(
        team_routes.manager_dashboard_service,
        "is_user_in_manager_scope",
        _fake_scope_check,
    )
    monkeypatch.setattr(
        team_routes.team_service, "get_user_by_id", _fake_get_user_by_id
    )
    monkeypatch.setattr(
        team_routes.reports_service,
        "generate_weekly_report",
        _fake_generate_weekly_report,
    )
    monkeypatch.setattr(team_routes, "log_access_event", _fake_log_access_event)

    response = await team_routes.export_weekly_report_for_team_member(
        user_id=user_id,
        current_user=current_user,  # type: ignore[arg-type]
        request=request,  # type: ignore[arg-type]
        week_start=date(2026, 4, 6),
        db=object(),  # type: ignore[arg-type]
    )

    assert response.status_code == 200
    assert response.body == b"# weekly report"
    assert (
        'attachment; filename="team_weekly_anna_2026-04-06_2026-04-12.md"'
        in response.headers["content-disposition"]
    )


@pytest.mark.asyncio
async def test_export_range_report_for_user_rejects_invalid_period() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await team_routes.export_range_report_for_user(
            user_id=uuid4(),
            current_user=SimpleNamespace(id=uuid4()),  # type: ignore[arg-type]
            request=_request_with_id(),  # type: ignore[arg-type]
            date_from=date(2026, 4, 10),
            date_to=date(2026, 4, 9),
            db=object(),  # type: ignore[arg-type]
        )

    assert exc_info.value.status_code == 422
    assert "date_to" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_export_range_report_for_user_404_when_user_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_get_user_by_id(*args: object, **kwargs: object) -> None:
        return None

    monkeypatch.setattr(
        team_routes.team_service, "get_user_by_id", _fake_get_user_by_id
    )

    with pytest.raises(HTTPException) as exc_info:
        await team_routes.export_range_report_for_user(
            user_id=uuid4(),
            current_user=SimpleNamespace(id=uuid4()),  # type: ignore[arg-type]
            request=_request_with_id(),  # type: ignore[arg-type]
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 8),
            db=object(),  # type: ignore[arg-type]
        )

    assert exc_info.value.status_code == 404
    assert "Пользователь не найден" in str(exc_info.value.detail)
