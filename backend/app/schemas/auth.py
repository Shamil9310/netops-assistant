from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.models.user import UserRole


class CurrentUserResponse(BaseModel):
    """Публичное представление пользователя в API-ответах."""

    id: str
    username: str
    full_name: str
    is_active: bool
    # Роль возвращаем фронтенду для управления навигацией и видимостью разделов.
    role: str


class ErrorResponse(BaseModel):
    detail: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=3, max_length=128)


class LoginResponse(BaseModel):
    message: str
    user: CurrentUserResponse


class LocalUserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    full_name: str = Field(min_length=3, max_length=128)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: str = Field(default=UserRole.EMPLOYEE.value)
    is_active: bool = True

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized_value = value.strip().lower()
        valid_roles = {role.value for role in UserRole}
        if normalized_value not in valid_roles:
            raise ValueError(f"Некорректная роль: {value}")
        return normalized_value


class LocalUserCreateResponse(BaseModel):
    user: CurrentUserResponse
    generated_password: str | None = None
