from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, _UNSAFE_BOOTSTRAP_PASSWORD, _UNSAFE_SECRET_KEY

# ---------------------------------------------------------------------------
# Локальная среда
# ---------------------------------------------------------------------------


def test_development_defaults_are_accepted() -> None:
    """Небезопасные дефолты допустимы в development — разработчик работает локально."""
    settings = Settings(
        _env_file=None,
        environment="development",
    )
    assert settings.environment == "development"
    assert settings.secret_key == _UNSAFE_SECRET_KEY
    assert settings.bootstrap_password == _UNSAFE_BOOTSTRAP_PASSWORD


def test_development_defaults_allow_non_secure_cookie() -> None:
    """В development secure-cookie не требуется — localhost работает по HTTP."""
    settings = Settings(
        _env_file=None,
        environment="development",
    )
    assert settings.effective_session_cookie_secure is False


def test_development_explicit_secure_cookie_is_respected() -> None:
    """Явное включение secure-cookie в development не должно блокироваться."""
    settings = Settings(
        _env_file=None,
        environment="development",
        session_cookie_secure=True,
    )
    assert settings.effective_session_cookie_secure is True


# ---------------------------------------------------------------------------
# Тестовая среда
# ---------------------------------------------------------------------------


def test_test_environment_rejects_unsafe_secret_key() -> None:
    """В test окружении небезопасный secret_key запрещён — иначе сессии тест/dev будут одинаковы."""
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            environment="test",
            # secret_key не задан, поэтому будет использовано небезопасное значение по умолчанию
        )


def test_test_environment_rejects_unsafe_bootstrap_password() -> None:
    """В test окружении дефолтный пароль bootstrap-пользователя запрещён."""
    with pytest.raises(ValidationError, match="BOOTSTRAP_PASSWORD"):
        Settings(
            _env_file=None,
            environment="test",
            secret_key="safe-test-key",
            bootstrap_username="test-engineer",
            # bootstrap_password не задан, поэтому будет использовано небезопасное значение по умолчанию
        )


def test_test_environment_rejects_unsafe_bootstrap_username() -> None:
    """В test окружении дефолтный username bootstrap-пользователя запрещён."""
    with pytest.raises(ValidationError, match="BOOTSTRAP_USERNAME"):
        Settings(
            _env_file=None,
            environment="test",
            secret_key="safe-test-key",
            bootstrap_password="safe-password",
            # bootstrap_username не задан, поэтому будет использовано небезопасное значение "engineer"
        )


def test_test_environment_rejects_all_unsafe_defaults_at_once() -> None:
    """Все небезопасные дефолты в test должны приводить к одной ошибке с перечнем проблем."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,
            environment="test",
        )
    error_message = str(exc_info.value)
    # Проверяем, что сообщение содержит информацию о всех трёх проблемах.
    assert "SECRET_KEY" in error_message
    assert "BOOTSTRAP_PASSWORD" in error_message
    assert "BOOTSTRAP_USERNAME" in error_message


def test_test_environment_accepts_safe_credentials() -> None:
    """Test окружение принимает конфиг с безопасными значениями."""
    settings = Settings(
        _env_file=None,
        environment="test",
        secret_key="safe-test-secret-key-32-chars-ok",
        bootstrap_username="test-engineer",
        bootstrap_password="safe-test-password-123",
        bootstrap_full_name="Test Engineer",
    )
    assert settings.environment == "test"


# ---------------------------------------------------------------------------
# Боевая среда
# ---------------------------------------------------------------------------


def test_production_defaults_force_secure_cookie() -> None:
    """В production secure-cookie включается автоматически — защита от передачи cookie по HTTP."""
    settings = Settings(
        _env_file=None,
        secret_key="prod-safe-key",
        bootstrap_username="prod-engineer",
        bootstrap_password="prod-safe-password",
        environment="production",
    )
    assert settings.effective_session_cookie_secure is True


def test_production_rejects_explicit_non_secure_cookie() -> None:
    """Production с явным session_cookie_secure=false — запрещён вне зависимости от остальных настроек."""
    with pytest.raises(ValidationError, match="SESSION_COOKIE_SECURE"):
        Settings(
            _env_file=None,
            secret_key="prod-safe-key",
            bootstrap_username="prod-engineer",
            bootstrap_password="prod-safe-password",
            environment="production",
            session_cookie_secure=False,
        )


def test_production_rejects_default_secret_key() -> None:
    """В production дефолтный secret_key запрещён — все сессии будут скомпрометированы."""
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            environment="production",
            session_cookie_secure=True,
            bootstrap_username="prod-engineer",
            bootstrap_password="prod-safe-password",
        )


def test_production_rejects_unsafe_bootstrap_credentials() -> None:
    """В production дефолтные bootstrap-credentials запрещены."""
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            environment="production",
            secret_key="prod-safe-key",
            session_cookie_secure=True,
            # bootstrap_username и bootstrap_password останутся небезопасными значениями по умолчанию
        )


def test_production_accepts_fully_safe_config() -> None:
    """Production принимает полностью безопасную конфигурацию."""
    settings = Settings(
        _env_file=None,
        environment="production",
        secret_key="prod-safe-secret-key-min-32-chars",
        session_cookie_secure=True,
        bootstrap_username="prod-engineer",
        bootstrap_password="Sup3r$afe!Passw0rd",
        bootstrap_full_name="Prod Engineer",
    )
    assert settings.environment == "production"
    assert settings.effective_session_cookie_secure is True


# ---------------------------------------------------------------------------
# Некорректный ввод
# ---------------------------------------------------------------------------


def test_invalid_environment_is_rejected() -> None:
    """Значение окружения ограничено допустимыми вариантами: development, test, production."""
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            secret_key="secret",
            environment="stage",  # type: ignore[arg-type]  # намеренно некорректное значение
        )


def test_effective_session_cookie_secure_explicit_override_in_production() -> None:
    """Явное session_cookie_secure=true в production должно работать корректно."""
    settings = Settings(
        _env_file=None,
        environment="production",
        secret_key="prod-safe-key",
        bootstrap_username="prod-engineer",
        bootstrap_password="prod-safe-password",
        session_cookie_secure=True,
    )
    assert settings.effective_session_cookie_secure is True
