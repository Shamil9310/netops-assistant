"""Тесты для auth-сервиса: хэширование паролей и токенов."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services.auth import (
    ensure_bootstrap_user,
    hash_password,
    hash_session_token,
    verify_password,
)

# ---------------------------------------------------------------------------
# Хэширование паролей
# ---------------------------------------------------------------------------


def test_hash_password_returns_non_empty_string() -> None:
    """Хэш пароля — непустая строка."""
    hashed_password = hash_password("my-password")
    assert isinstance(hashed_password, str)
    assert len(hashed_password) > 0


def test_verify_password_accepts_correct_password() -> None:
    """Правильный пароль проходит верификацию."""
    password = "super-secret-123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_wrong_password() -> None:
    """Неверный пароль не проходит верификацию."""
    hashed = hash_password("correct-password")
    assert verify_password("wrong-password", hashed) is False


def test_hash_password_is_not_plaintext() -> None:
    """Хэш пароля не равен исходному паролю."""
    password = "my-secret"
    assert hash_password(password) != password


def test_two_hashes_of_same_password_differ() -> None:
    """Два хэша одного пароля должны отличаться (argon2 использует соль)."""
    password = "same-password"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2


# ---------------------------------------------------------------------------
# Хэширование токенов сессий
# ---------------------------------------------------------------------------


def test_hash_session_token_is_deterministic() -> None:
    """Хэш токена детерминирован — одинаковый токен даёт одинаковый хэш."""
    token = "my-session-token"
    assert hash_session_token(token) == hash_session_token(token)


def test_hash_session_token_different_tokens_differ() -> None:
    """Разные токены дают разные хэши."""
    assert hash_session_token("token-a") != hash_session_token("token-b")


def test_hash_session_token_is_not_plaintext() -> None:
    """Хэш токена не равен самому токену."""
    token = "raw-token"
    assert hash_session_token(token) != token


def test_hash_session_token_returns_hex_string() -> None:
    """Хэш токена — строка в hex-формате (SHA-256 = 64 символа)."""
    session_hash = hash_session_token("any-token")
    assert len(session_hash) == 64
    assert all(c in "0123456789abcdef" for c in session_hash)


def test_verify_password_empty_password_raises_or_fails() -> None:
    """Пустой пароль не должен совпадать с хэшем непустого."""
    hashed = hash_password("non-empty")
    assert verify_password("", hashed) is False


class _BootstrapSessionStub:
    def __init__(self) -> None:
        self.executed_statements: list[object] = []
        self.added_user = None
        self.committed = False

    async def execute(self, statement: object) -> object:
        self.executed_statements.append(statement)
        return SimpleNamespace()

    def add(self, user: object) -> None:
        self.added_user = user

    async def commit(self) -> None:
        self.committed = True


@pytest.mark.asyncio
async def test_ensure_bootstrap_user_creates_only_missing_bootstrap_user(
    monkeypatch,
) -> None:
    """Bootstrap создаётся один раз и не затрагивает существующих пользователей."""
    session = _BootstrapSessionStub()

    async def _get_user_by_username(_session: object, _username: str) -> object | None:
        return None

    monkeypatch.setattr("app.services.auth.get_user_by_username", _get_user_by_username)

    await ensure_bootstrap_user(session)

    assert session.committed is True
    assert session.added_user is not None
    assert session.added_user.username == settings.bootstrap_username
    assert session.added_user.full_name == settings.bootstrap_full_name
    assert session.added_user.role == "developer"


@pytest.mark.asyncio
async def test_ensure_bootstrap_user_is_noop_when_user_exists(monkeypatch) -> None:
    """Повторный запуск не должен удалять или перезаписывать локальных пользователей."""
    session = _BootstrapSessionStub()
    existing_user = SimpleNamespace(
        username=settings.bootstrap_username,
        full_name="Original Name",
        password_hash="original-hash",
        is_active=False,
        role="employee",
    )

    async def _get_user_by_username(_session: object, _username: str) -> object | None:
        return existing_user

    monkeypatch.setattr("app.services.auth.get_user_by_username", _get_user_by_username)

    await ensure_bootstrap_user(session)

    assert session.committed is False
    assert session.added_user is None
    assert existing_user.full_name == "Original Name"
    assert existing_user.password_hash == "original-hash"
    assert existing_user.is_active is False
    assert existing_user.role == "employee"
