"""Тесты для auth-сервиса: хэширование паролей и токенов."""

from __future__ import annotations

import pytest

from app.services.auth import hash_password, hash_session_token, verify_password


# ---------------------------------------------------------------------------
# Хэширование паролей
# ---------------------------------------------------------------------------


def test_hash_password_returns_non_empty_string() -> None:
    """Хэш пароля — непустая строка."""
    result = hash_password("my-password")
    assert isinstance(result, str)
    assert len(result) > 0


def test_verify_password_happy_path() -> None:
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
    result = hash_session_token("any-token")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_verify_password_empty_password_raises_or_fails() -> None:
    """Пустой пароль не должен совпадать с хэшем непустого."""
    hashed = hash_password("non-empty")
    assert verify_password("", hashed) is False
