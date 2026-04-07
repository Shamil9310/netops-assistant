from __future__ import annotations

from pydantic import BaseModel, Field


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
