"""Тесты модуля структурированного логирования.

Проверяем:
- JSON-форматтер выдаёт валидный JSON с нужными полями;
- request_id_var корректно хранит и сбрасывает значение;
- configure_logging не падает ни в одном режиме окружения.
"""

from __future__ import annotations

import json
import logging

import pytest

from app.core.logging import JsonFormatter, configure_logging, request_id_var


def _make_record(message: str, level: int = logging.INFO) -> logging.LogRecord:
    """Создаёт тестовую запись лога с заданным сообщением и уровнем."""
    record = logging.LogRecord(
        name="test.logger",
        level=level,
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    return record


def test_json_formatter_produces_valid_json() -> None:
    """JsonFormatter должен возвращать строку, которая парсится как JSON."""
    formatter = JsonFormatter()
    record = _make_record("тестовое сообщение")
    output = formatter.format(record)
    parsed = json.loads(output)
    assert isinstance(parsed, dict)


def test_json_formatter_contains_required_fields() -> None:
    """JSON-запись должна содержать timestamp, level, logger, message."""
    formatter = JsonFormatter()
    record = _make_record("проверка полей")
    parsed = json.loads(formatter.format(record))
    assert "timestamp" in parsed
    assert "level" in parsed
    assert "logger" in parsed
    assert "message" in parsed


def test_json_formatter_message_matches() -> None:
    """Поле message в JSON должно совпадать с оригинальным сообщением."""
    formatter = JsonFormatter()
    msg = "конкретное сообщение для теста"
    record = _make_record(msg)
    parsed = json.loads(formatter.format(record))
    assert parsed["message"] == msg


def test_json_formatter_level_matches() -> None:
    """Поле level должно отражать реальный уровень лога."""
    formatter = JsonFormatter()
    record = _make_record("ошибка", level=logging.ERROR)
    parsed = json.loads(formatter.format(record))
    assert parsed["level"] == "ERROR"


def test_json_formatter_includes_request_id_when_set() -> None:
    """Если request_id установлен в контексте, он должен попасть в JSON."""
    formatter = JsonFormatter()
    token = request_id_var.set("test-request-id-123")
    try:
        record = _make_record("запрос с id")
        parsed = json.loads(formatter.format(record))
        assert parsed.get("request_id") == "test-request-id-123"
    finally:
        request_id_var.reset(token)


def test_json_formatter_no_request_id_when_not_set() -> None:
    """Если request_id не установлен, поле request_id не должно быть в JSON."""
    formatter = JsonFormatter()
    # Гарантируем что контекст чистый.
    token = request_id_var.set(None)
    try:
        record = _make_record("запрос без id")
        parsed = json.loads(formatter.format(record))
        assert "request_id" not in parsed
    finally:
        request_id_var.reset(token)


def test_request_id_var_is_isolated() -> None:
    """Сброс токена должен восстанавливать предыдущее значение."""
    original = request_id_var.get()
    token = request_id_var.set("temporary-id")
    assert request_id_var.get() == "temporary-id"
    request_id_var.reset(token)
    assert request_id_var.get() == original


@pytest.mark.parametrize("env", ["development", "test", "production"])
def test_configure_logging_does_not_raise(env: str) -> None:
    """configure_logging должен отрабатывать без исключений для любого окружения."""
    configure_logging(env)
