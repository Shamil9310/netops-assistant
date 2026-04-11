"""Тесты аналитического дашборда журнала."""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

import app.services.dashboard as dashboard_service


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):  # type: ignore[override]
        return datetime(2026, 4, 10, 12, 0, tzinfo=tz or UTC)


@pytest.mark.asyncio
async def test_build_analytics_dashboard_aggregates_day_week_and_services(
    monkeypatch,
) -> None:
    fixed_today = date(2026, 4, 10)
    user_id = uuid4()

    entries = [
        SimpleNamespace(
            user_id=user_id,
            work_date=fixed_today,
            ticket_number="SR1",
            external_ref=None,
            service="TrueConf",
        ),
        SimpleNamespace(
            user_id=user_id,
            work_date=date(2026, 4, 9),
            ticket_number="SR2",
            external_ref=None,
            service="Netbox",
        ),
        SimpleNamespace(
            user_id=user_id,
            work_date=date(2026, 3, 28),
            ticket_number="SR3",
            external_ref=None,
            service="Netbox",
        ),
    ]

    class FakeResult:
        def scalars(self):
            return self

        def all(self):
            return entries

    class FakeSession:
        async def execute(self, statement):  # noqa: ARG002
            return FakeResult()

    monkeypatch.setattr(dashboard_service, "datetime", FrozenDateTime)

    analytics = await dashboard_service.build_analytics_dashboard(
        FakeSession(),
        user_id,
    )

    assert analytics.period_start == date(2026, 3, 12)
    assert analytics.period_end == fixed_today
    assert analytics.today_total == 1
    assert analytics.week_total == 2
    assert analytics.total_entries == 3
    assert analytics.service_breakdown[0].service == "Netbox"
    assert analytics.service_breakdown[0].total == 2
    assert analytics.daily_series[-1].total == 1
