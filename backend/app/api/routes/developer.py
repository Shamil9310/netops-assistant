from typing import Annotated
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import require_developer
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    CurrentUserResponse,
    LocalUserCreateRequest,
    LocalUserCreateResponse,
)
from app.services.auth import LocalUserCreateError, create_local_user, delete_local_user
from app.services import team as team_service
from app.services.developer_metrics import build_summary_payload

router = APIRouter()

CurrentDeveloper = Annotated[User, Depends(require_developer)]


@router.get("/summary")
async def developer_summary(
    _: CurrentDeveloper,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    database_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        database_ok = False
    return build_summary_payload(database_ok=database_ok)


@router.get("/diagnostics")
async def developer_diagnostics(
    _: CurrentDeveloper,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
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


@router.post(
    "/users/local",
    status_code=status.HTTP_201_CREATED,
    response_model=LocalUserCreateResponse,
)
async def create_local_user_account(
    payload: LocalUserCreateRequest,
    _: CurrentDeveloper,
    db: AsyncSession = Depends(get_db),
) -> LocalUserCreateResponse:
    """Создаёт локальную учётную запись с ролью employee/manager/developer."""
    try:
        result = await create_local_user(
            db,
            username=payload.username,
            full_name=payload.full_name,
            password=payload.password,
            role=payload.role,
            is_active=payload.is_active,
        )
    except LocalUserCreateError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    user = result.user
    return LocalUserCreateResponse(
        user=CurrentUserResponse(
            id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            role=user.role,
        ),
        generated_password=result.generated_password,
    )


@router.delete(
    "/users/local/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_local_user_account(
    user_id: UUID,
    current_user: CurrentDeveloper,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удаляет локальную учётную запись. Разработчик не может удалить сам себя."""
    try:
        await delete_local_user(
            db,
            target_user_id=user_id,
            actor_user_id=current_user.id,
        )
    except LocalUserCreateError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get(
    "/users/local",
    response_model=list[CurrentUserResponse],
)
async def list_local_users(
    _: CurrentDeveloper,
    db: AsyncSession = Depends(get_db),
) -> list[CurrentUserResponse]:
    """Возвращает список локальных пользователей для экрана управления УЗ."""
    users = await team_service.get_all_users(db)
    return [
        CurrentUserResponse(
            id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            role=user.role,
        )
        for user in users
    ]
