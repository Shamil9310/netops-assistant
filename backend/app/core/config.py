from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Небезопасные значения по умолчанию, которые запрещено использовать
# в тестовой и боевой среде. Вынесены в константы, чтобы не было "магических строк".
_UNSAFE_SECRET_KEY = "dev-only-change-me"
_UNSAFE_BOOTSTRAP_PASSWORD = "12345678"
_UNSAFE_BOOTSTRAP_USERNAME = "shamil.isaev"
_BACKEND_ROOT_DIR = Path(__file__).resolve().parents[2]
_BACKEND_ENV_FILE = _BACKEND_ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Централизованные настройки backend-приложения."""

    # Используем абсолютный путь к файлу backend/.env, чтобы настройки не зависели
    # от текущей рабочей директории процесса.
    model_config = SettingsConfigDict(
        env_prefix="NETOPS_ASSISTANT_",
        env_file=_BACKEND_ENV_FILE,
        extra="ignore",
    )

    app_name: str = "NetOps Assistant API"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = (
        "postgresql+asyncpg://netops:netops@localhost:5432/netops_assistant"
    )
    secret_key: str = _UNSAFE_SECRET_KEY
    cors_origins: list[str] = ["http://localhost:3000"]
    cors_methods: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    cors_headers: list[str] = ["Content-Type", "X-CSRF-Token", "X-Request-ID"]
    session_cookie_name: str = "netops_session"
    csrf_cookie_name: str = "netops_csrf"
    session_ttl_hours: int = 12
    session_cookie_secure: bool | None = None
    export_retention_days: int = 30
    bootstrap_username: str = _UNSAFE_BOOTSTRAP_USERNAME
    bootstrap_password: str = _UNSAFE_BOOTSTRAP_PASSWORD
    bootstrap_full_name: str = "Шамиль Исаев"
    auth_provider: Literal["local", "ldap"] = "local"
    ldap_server_url: str | None = None
    ldap_base_dn: str | None = None
    ldap_bind_dn_template: str = "{username}"
    ldap_user_filter: str = "(sAMAccountName={username})"
    ldap_group_role_map: str = ""
    ldap_default_role: str = "employee"
    ldap_use_tls: bool = True
    ldap_tls_validate: bool = True
    ldap_fallback_to_local: bool = True

    @property
    def effective_session_cookie_secure(self) -> bool:
        """Возвращает флаг secure для session cookie с учётом окружения.

        Если значение задано явно — используем его.
        Иначе: в production всегда true, в остальных — false.
        """
        if self.session_cookie_secure is not None:
            return self.session_cookie_secure
        return self.environment == "production"

    @model_validator(mode="after")
    def validate_security_constraints(self) -> Settings:
        """Проверяет требования безопасности в зависимости от окружения.

        В development допускаются небезопасные дефолты — удобно для локальной работы.
        В test и production небезопасные дефолты запрещены: они могут привести
        к компрометации данных или утечке сессий.
        """
        if self.environment == "development":
            # В локальной среде эти ограничения не применяем:
            # локальная среда нужна для быстрого старта.
            return self

        # Общие проверки для тестовой и боевой среды.
        errors: list[str] = []

        if self.secret_key == _UNSAFE_SECRET_KEY:
            errors.append(
                f"NETOPS_ASSISTANT_SECRET_KEY не может быть '{_UNSAFE_SECRET_KEY}' "
                f"в окружении '{self.environment}' — задайте уникальный ключ"
            )

        if self.bootstrap_password == _UNSAFE_BOOTSTRAP_PASSWORD:
            errors.append(
                "NETOPS_ASSISTANT_BOOTSTRAP_PASSWORD не может быть "
                f"'{_UNSAFE_BOOTSTRAP_PASSWORD}' "
                f"в окружении '{self.environment}' — задайте надёжный пароль"
            )

        if self.bootstrap_username == _UNSAFE_BOOTSTRAP_USERNAME:
            errors.append(
                "NETOPS_ASSISTANT_BOOTSTRAP_USERNAME не может быть "
                f"'{_UNSAFE_BOOTSTRAP_USERNAME}' "
                f"в окружении '{self.environment}' — задайте "
                "уникальное имя пользователя"
            )

        # Дополнительные требования только для боевой среды.
        if self.environment == "production":
            if not self.effective_session_cookie_secure:
                errors.append(
                    "NETOPS_ASSISTANT_SESSION_COOKIE_SECURE должен быть true "
                    "в production — "
                    "передача cookie без HTTPS небезопасна"
                )
            if self.auth_provider == "ldap":
                if not self.ldap_server_url:
                    errors.append(
                        "NETOPS_ASSISTANT_LDAP_SERVER_URL обязателен "
                        "для LDAP режима в production"
                    )
                if not self.ldap_base_dn:
                    errors.append(
                        "NETOPS_ASSISTANT_LDAP_BASE_DN обязателен "
                        "для LDAP режима в production"
                    )

        if errors:
            # Объединяем все ошибки в одно сообщение,
            # чтобы можно было исправить всё за один проход.
            raise ValueError(
                "Ошибки конфигурации безопасности:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

        return self


settings = Settings()
