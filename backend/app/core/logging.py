"""Настройка структурированного логирования.

В production используется JSON-формат для удобной агрегации в ELK/Loki/etc.
В development используется читаемый текстовый формат.

Correlation ID берётся из request_id, проставленного middleware в main.py.
Каждая запись в логах содержит:
- timestamp в ISO 8601;
- уровень лога;
- имя логгера (модуль);
- сообщение;
- request_id (если доступен через contextvars).
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Переменная контекста для хранения request_id текущего запроса.
# Устанавливается в middleware и читается в форматтере.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    """Форматтер, выводящий каждую запись лога как JSON-объект на одной строке.

    Удобен для парсинга в системах агрегации логов (ELK, Grafana Loki).
    Добавляет request_id из контекста, если он установлен.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON-строку."""
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_var.get()
        if request_id:
            payload["request_id"] = request_id

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(environment: str) -> None:
    """Настраивает глобальное логирование в зависимости от окружения.

    В production — JSON-формат для агрегации.
    В development и test — читаемый текстовый формат.

    Вызывается один раз при старте приложения из lifespan.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Убираем все существующие хендлеры, чтобы не было дублирования.
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if environment == "production":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

    # Уменьшаем шум от сторонних библиотек.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
