"""Тесты сервиса метрик для панели разработчика."""

from __future__ import annotations

import time

from app.services.developer_metrics import (
    build_summary_payload,
    get_disk_usage_percent,
    get_uptime_seconds,
)


def test_get_uptime_seconds_non_negative() -> None:
    """Проверяет, что время работы не уходит в отрицательное значение."""
    assert get_uptime_seconds() >= 0


def test_get_uptime_seconds_grows_over_time() -> None:
    """Проверяет, что время работы растёт при последовательных вызовах."""
    first = get_uptime_seconds()
    time.sleep(0.01)
    second = get_uptime_seconds()
    assert second >= first


def test_get_disk_usage_percent_range() -> None:
    """Проверяет, что процент диска всегда в диапазоне 0..100."""
    value = get_disk_usage_percent("/")
    assert 0.0 <= value <= 100.0


def test_build_summary_payload_contains_widgets() -> None:
    """Проверяет структуру данных для панели разработчика."""
    payload = build_summary_payload(database_ok=True)
    widgets = payload.get("widgets")
    assert isinstance(widgets, dict)
    assert "load_avg_1m" in widgets
    assert "disk_usage_percent" in widgets
    assert "uptime_seconds" in widgets
    assert widgets.get("database_ok") is True
