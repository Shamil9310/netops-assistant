from __future__ import annotations

from pydantic import BaseModel, Field


class TeamMemberResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    is_active: bool


class TeamResponse(BaseModel):
    id: str
    name: str
    description: str | None
    manager_id: str | None
    members: list[TeamMemberResponse]


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    description: str | None = None
    manager_id: str | None = None


class TeamUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=128)
    description: str | None = None
    manager_id: str | None = None


class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    is_active: bool
    teams: list[str]


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    full_name: str = Field(min_length=2, max_length=128)
    password: str = Field(min_length=8, max_length=256)
    role: str


class UserUpdateRoleRequest(BaseModel):
    role: str


class TeamWeeklySummaryResponse(BaseModel):
    """Недельная сводка по сотруднику для панели руководителя."""

    user_id: str
    username: str
    full_name: str
    total_entries: int
    by_status: dict[str, int]
    by_activity_type: dict[str, int]
