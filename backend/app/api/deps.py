from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.auth import get_current_user


async def _get_authenticated_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    session_token: Annotated[str | None, Cookie(alias=settings.session_cookie_name)] = None,
) -> User:
    """Возвращает текущего аутентифицированного пользователя из session cookie.

    Если пользователь не авторизован или сессия истекла — HTTP 401.
    Используется как базовая dependency для всех защищённых endpoint'ов.
    """
    user = await get_current_user(db, session_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )
    return user


def _require_role(*allowed_roles: UserRole):
    """Фабрика dependency для проверки роли пользователя.

    Создаёт dependency, который пропускает только пользователей с указанными ролями.
    Пользователи с недостаточной ролью получают HTTP 403.

    Пример использования:
    ```python
    @router.get("/team", dependencies=[Depends(require_manager_or_developer)])
    async def team_data(user: CurrentUser) -> ...:
        ...
    ```
    """
    allowed_set = {role.value for role in allowed_roles}

    async def _check_role(user: Annotated[User, Depends(_get_authenticated_user)]) -> User:
        if user.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ запрещён. Требуется одна из ролей: {', '.join(allowed_set)}",
            )
        return user

    return _check_role


# Аннотированный тип для аутентифицированного пользователя (любая роль).
CurrentUser = Annotated[User, Depends(_get_authenticated_user)]

# Dependency-функции для проверки конкретных ролей.
# Используются через Depends() в роутах.
require_employee = _require_role(UserRole.EMPLOYEE, UserRole.MANAGER, UserRole.DEVELOPER)
require_manager = _require_role(UserRole.MANAGER, UserRole.DEVELOPER)
require_developer = _require_role(UserRole.DEVELOPER)
