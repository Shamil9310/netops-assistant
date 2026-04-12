"""Тесты Pydantic-схем аутентификации."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    LocalUserCreateRequest,
)


class TestLoginRequest:
    def test_valid(self):
        req = LoginRequest(username="admin", password="secret123")
        assert req.username == "admin"
        assert req.password == "secret123"

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="ab", password="secret123")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="admin", password="ab")

    def test_username_too_long(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="a" * 65, password="secret123")


class TestLocalUserCreateRequest:
    def test_valid_defaults(self):
        req = LocalUserCreateRequest(username="newuser", full_name="Иван Иванов")
        assert req.role == "employee"
        assert req.is_active is True
        assert req.password is None

    def test_role_normalized_to_lowercase(self):
        req = LocalUserCreateRequest(
            username="newuser", full_name="Иван Иванов", role="MANAGER"
        )
        assert req.role == "manager"

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            LocalUserCreateRequest(
                username="newuser", full_name="Иван Иванов", role="superadmin"
            )

    def test_password_optional(self):
        req = LocalUserCreateRequest(username="newuser", full_name="Иван Иванов")
        assert req.password is None

    def test_password_min_length(self):
        with pytest.raises(ValidationError):
            LocalUserCreateRequest(
                username="newuser", full_name="Иван Иванов", password="short"
            )

    def test_full_name_too_short(self):
        with pytest.raises(ValidationError):
            LocalUserCreateRequest(username="newuser", full_name="ab")


class TestCurrentUserResponse:
    def test_valid(self):
        resp = CurrentUserResponse(
            id="uuid-1",
            username="admin",
            full_name="Администратор",
            is_active=True,
            role="developer",
        )
        assert resp.id == "uuid-1"
        assert resp.role == "developer"
