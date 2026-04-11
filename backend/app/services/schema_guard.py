from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

_BACKEND_ROOT_DIR = Path(__file__).resolve().parents[2]
_ALEMBIC_CONFIG_PATH = _BACKEND_ROOT_DIR / "alembic.ini"
_ALEMBIC_SCRIPT_PATH = _BACKEND_ROOT_DIR / "alembic"


class SchemaVersionMismatchError(RuntimeError):
    """Сигнализирует, что код backend и схема БД не совпадают."""


def get_expected_schema_revision() -> str:
    """Возвращает актуальную ревизию схемы из Alembic.

    Бизнес-смысл этой проверки:
    backend не должен запускаться, если код ожидает более новую схему,
    чем реально применена в базе данных. Иначе пользователь увидит
    случайные 500-ошибки уже во время работы интерфейса.
    """
    alembic_config = Config(str(_ALEMBIC_CONFIG_PATH))
    alembic_config.set_main_option("script_location", str(_ALEMBIC_SCRIPT_PATH))
    script_directory = ScriptDirectory.from_config(alembic_config)
    current_head = script_directory.get_current_head()

    if current_head is None:
        raise RuntimeError("Не удалось определить актуальную ревизию Alembic")

    return current_head


async def get_applied_schema_revision(session: AsyncSession) -> str | None:
    """Возвращает ревизию схемы, реально применённую в подключённой БД."""
    result = await session.execute(text("SELECT version_num FROM alembic_version"))
    return result.scalar_one_or_none()


async def ensure_schema_is_current(session: AsyncSession) -> None:
    """Проверяет, что backend работает с актуальной схемой БД.

    Если ревизии не совпадают, намеренно останавливаем запуск приложения.
    Это безопаснее, чем допустить частично рабочий backend с неочевидными
    сбоями на отдельных endpoint.
    """
    expected_revision = get_expected_schema_revision()

    try:
        applied_revision = await get_applied_schema_revision(session)
    except SQLAlchemyError as exc:
        raise SchemaVersionMismatchError(
            "Не удалось прочитать версию схемы БД. "
            "Проверь доступность таблицы alembic_version и выполни "
            "`alembic upgrade head`."
        ) from exc

    if applied_revision != expected_revision:
        applied_label = applied_revision or "отсутствует"
        raise SchemaVersionMismatchError(
            "Схема БД неактуальна: "
            f"ожидается ревизия `{expected_revision}`, "
            f"но найдена `{applied_label}`. "
            "Перед запуском backend выполни `alembic upgrade head`."
        )
