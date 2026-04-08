from __future__ import annotations

from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.core.config import settings
from app.db.session import get_db
from app.schemas.auth import (
    CurrentUserResponse,
    ErrorResponse,
    LoginRequest,
    LoginResponse,
)
from app.services.auth import authenticate_user, create_session, revoke_session

router = APIRouter()


def _to_current_user_response(user: CurrentUser) -> CurrentUserResponse:
    """Преобразует ORM-модель User в схему ответа API."""
    return CurrentUserResponse(
        id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        role=user.role,
    )


@router.post(
    "/login", response_model=LoginResponse, responses={401: {"model": ErrorResponse}}
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Аутентифицирует пользователя и выдаёт session cookie.

    Передаём client_ip для записи в auth audit log — позволяет обнаружить брутфорс.
    """
    client_ip = request.client.host if request.client else None
    user = await authenticate_user(
        db, payload.username, payload.password, client_ip=client_ip
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    session_token = await create_session(db, user)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=settings.effective_session_cookie_secure,
        max_age=settings.session_ttl_hours * 60 * 60,
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=token_urlsafe(24),
        httponly=False,
        samesite="lax",
        secure=settings.effective_session_cookie_secure,
        max_age=settings.session_ttl_hours * 60 * 60,
    )
    return LoginResponse(message="Вход выполнен", user=_to_current_user_response(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> None:
    """Завершает сессию пользователя и удаляет session cookie."""
    session_token = request.cookies.get(settings.session_cookie_name)
    client_ip = request.client.host if request.client else None
    if session_token:
        await revoke_session(db, session_token, client_ip=client_ip)
    response.delete_cookie(settings.session_cookie_name)
    response.delete_cookie(settings.csrf_cookie_name)


@router.get(
    "/me", response_model=CurrentUserResponse, responses={401: {"model": ErrorResponse}}
)
async def me(current_user: CurrentUser) -> CurrentUserResponse:
    """Возвращает данные текущего аутентифицированного пользователя."""
    return _to_current_user_response(current_user)
