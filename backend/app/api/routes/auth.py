from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.auth import CurrentUserResponse, ErrorResponse, LoginRequest, LoginResponse
from app.services.auth import authenticate_user, create_session, get_current_user, revoke_session

router = APIRouter()


def to_current_user_response(user) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
    )


@router.post("/login", response_model=LoginResponse, responses={401: {"model": ErrorResponse}})
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    user = await authenticate_user(db, payload.username, payload.password)
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
        secure=False,
        max_age=settings.session_ttl_hours * 60 * 60,
    )
    return LoginResponse(message="Вход выполнен", user=to_current_user_response(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)) -> Response:
    session_token = request.cookies.get(settings.session_cookie_name)
    if session_token:
        await revoke_session(db, session_token)
    response.delete_cookie(settings.session_cookie_name)
    return response


@router.get("/me", response_model=CurrentUserResponse, responses={401: {"model": ErrorResponse}})
async def me(request: Request, db: AsyncSession = Depends(get_db)) -> CurrentUserResponse:
    user = await get_current_user(db, request.cookies.get(settings.session_cookie_name))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")
    return to_current_user_response(user)
