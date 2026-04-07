from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.db.session import get_db
from app.services.developer_metrics import build_summary_payload

router = APIRouter()


@router.get("/summary")
async def developer_summary(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    database_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        database_ok = False
    return build_summary_payload(database_ok=database_ok)


@router.get("/diagnostics")
async def developer_diagnostics(db: AsyncSession = Depends(get_db)) -> dict[str, object]:
    """Сервисный endpoint для базовой диагностики среды выполнения."""
    database_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        database_ok = False

    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "database_ok": database_ok,
    }
