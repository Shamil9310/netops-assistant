from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("")
def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "timestamp": datetime.now(UTC).isoformat(),
    }
