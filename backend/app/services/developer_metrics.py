from __future__ import annotations

import os
import shutil
import time
from datetime import UTC, datetime

APP_START_MONOTONIC = time.monotonic()


def get_uptime_seconds() -> int:
    """Возвращает время работы серверного процесса в секундах."""
    return int(time.monotonic() - APP_START_MONOTONIC)


def get_disk_usage_percent(path: str = "/") -> float:
    """Возвращает процент использования диска для указанного пути."""
    usage = shutil.disk_usage(path)
    used = usage.total - usage.free
    if usage.total == 0:
        return 0.0
    return round((used / usage.total) * 100, 2)


def get_load_average_1m() -> float:
    """Возвращает среднюю загрузку CPU за 1 минуту (если доступно)."""
    try:
        return round(os.getloadavg()[0], 2)
    except OSError:
        return 0.0


def build_summary_payload(database_ok: bool) -> dict[str, object]:
    """Собирает данные для панели разработчика с базовыми системными метриками."""
    return {
        "module": "developer",
        "status": "ok",
        "captured_at": datetime.now(UTC).isoformat(),
        "widgets": {
            "load_avg_1m": get_load_average_1m(),
            "disk_usage_percent": get_disk_usage_percent("/"),
            "uptime_seconds": get_uptime_seconds(),
            "database_ok": database_ok,
        },
    }
