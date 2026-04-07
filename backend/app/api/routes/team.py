from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, require_developer, require_manager
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.team import (
    TeamCreateRequest,
    TeamMemberResponse,
    TeamResponse,
    TeamWeeklySummaryResponse,
    TeamUpdateRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRoleRequest,
)
from app.services import manager_dashboard as manager_dashboard_service
from app.services import reports as reports_service
from app.services import team as team_service
from app.services.access_audit import log_access_event
from app.services.auth import get_user_by_username, hash_password

router = APIRouter()


def _to_team_response(team: object) -> TeamResponse:
    """Преобразует ORM-модель Team в схему ответа API."""
    return TeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        manager_id=str(team.manager_id) if team.manager_id else None,
        members=[
            TeamMemberResponse(
                id=str(m.id),
                username=m.username,
                full_name=m.full_name,
                role=m.role,
                is_active=m.is_active,
            )
            for m in team.members
        ],
    )


def _to_user_response(user: User) -> UserResponse:
    """Преобразует ORM-модель User в схему ответа API."""
    return UserResponse(
        id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        teams=[t.name for t in user.teams],
    )


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------


@router.get("/teams", response_model=list[TeamResponse], dependencies=[Depends(require_manager)])
async def list_teams(db: AsyncSession = Depends(get_db)) -> list[TeamResponse]:
    """Список всех команд. Доступен менеджерам и разработчикам."""
    teams = await team_service.get_all_teams(db)
    return [_to_team_response(t) for t in teams]


@router.post(
    "/teams",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_developer)],
)
async def create_team(payload: TeamCreateRequest, db: AsyncSession = Depends(get_db)) -> TeamResponse:
    """Создаёт новую команду. Только developer."""
    team = await team_service.create_team(db, payload.name, payload.description, payload.manager_id)
    return _to_team_response(team)


@router.patch("/teams/{team_id}", response_model=TeamResponse, dependencies=[Depends(require_developer)])
async def update_team(
    team_id: UUID,
    payload: TeamUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """Обновляет данные команды. Только developer."""
    team = await team_service.get_team_by_id(db, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команда не найдена")
    updated = await team_service.update_team(db, team, payload.name, payload.description, payload.manager_id)
    return _to_team_response(updated)


@router.post(
    "/teams/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_developer)],
)
async def add_member(team_id: UUID, user_id: UUID, db: AsyncSession = Depends(get_db)) -> None:
    """Добавляет пользователя в команду. Только developer."""
    team = await team_service.get_team_by_id(db, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команда не найдена")
    user = await team_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    await team_service.add_member_to_team(db, team, user)


@router.delete(
    "/teams/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_developer)],
)
async def remove_member(team_id: UUID, user_id: UUID, db: AsyncSession = Depends(get_db)) -> None:
    """Удаляет пользователя из команды. Только developer."""
    team = await team_service.get_team_by_id(db, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Команда не найдена")
    user = await team_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    await team_service.remove_member_from_team(db, team, user)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_manager)])
async def list_users(db: AsyncSession = Depends(get_db)) -> list[UserResponse]:
    """Список всех пользователей. Доступен менеджерам и разработчикам."""
    users = await team_service.get_all_users(db)
    return [_to_user_response(u) for u in users]


@router.get("/users/my-team", response_model=list[UserResponse])
async def my_team_members(current_user: CurrentUser, db: AsyncSession = Depends(get_db)) -> list[UserResponse]:
    """Возвращает участников команд текущего менеджера.

    Менеджер видит только своих подчинённых — ключевое ограничение видимости данных.
    """
    members = await team_service.get_team_members_for_manager(db, current_user.id)
    return [_to_user_response(u) for u in members]


@router.get(
    "/users/my-team/summary/weekly",
    response_model=list[TeamWeeklySummaryResponse],
    dependencies=[Depends(require_manager)],
)
async def my_team_weekly_summary(
    current_user: CurrentUser,
    week_start: date = Query(..., description="Понедельник недели в формате YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
) -> list[TeamWeeklySummaryResponse]:
    """Возвращает недельную сводку по сотрудникам manager scope."""
    summaries = await manager_dashboard_service.get_weekly_team_summary(db, current_user.id, week_start)
    return [
        TeamWeeklySummaryResponse(
            user_id=str(item.user_id),
            username=item.username,
            full_name=item.full_name,
            total_entries=item.total_entries,
            by_status=item.by_status,
            by_activity_type=item.by_activity_type,
        )
        for item in summaries
    ]


@router.get(
    "/users/{user_id}/reports/weekly/export/md",
    dependencies=[Depends(require_manager)],
)
async def export_weekly_report_for_team_member(
    user_id: UUID,
    current_user: CurrentUser,
    request: Request,
    week_start: date = Query(..., description="Понедельник недели в формате YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Экспортирует недельный отчёт сотрудника, если он в manager scope."""
    in_scope = await manager_dashboard_service.is_user_in_manager_scope(db, current_user.id, user_id)
    if not in_scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Сотрудник не относится к вашей команде",
        )

    team_member = await team_service.get_user_by_id(db, user_id)
    if team_member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    content_md = await reports_service.generate_weekly_report(
        db,
        user_id=user_id,
        week_start=week_start,
        author_name=team_member.full_name,
    )
    await log_access_event(
        db,
        user_id=current_user.id,
        target_user_id=user_id,
        resource_type="team_weekly_report",
        resource_id=f"{user_id}:{week_start.isoformat()}",
        action="export_md",
        request_id=getattr(request.state, "request_id", None),
    )
    week_end = week_start + timedelta(days=6)
    filename = f"team_weekly_{team_member.username}_{week_start.isoformat()}_{week_end.isoformat()}.md"
    return Response(
        content=content_md.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_developer)],
)
async def create_user(payload: UserCreateRequest, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """Создаёт нового пользователя. Только developer."""
    existing = await get_user_by_username(db, payload.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким именем уже существует",
        )

    if payload.role not in {r.value for r in UserRole}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Недопустимая роль: {payload.role}",
        )

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _to_user_response(user)


@router.patch("/users/{user_id}/role", response_model=UserResponse, dependencies=[Depends(require_developer)])
async def update_user_role(
    user_id: UUID,
    payload: UserUpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Изменяет роль пользователя. Только developer."""
    if payload.role not in {r.value for r in UserRole}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Недопустимая роль: {payload.role}",
        )

    user = await team_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return _to_user_response(user)
