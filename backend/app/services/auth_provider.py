from __future__ import annotations

import logging
import ssl
from dataclasses import dataclass
from typing import Protocol

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

_password_hasher = PasswordHash.recommended()


@dataclass(slots=True)
class AuthenticatedIdentity:
    """Данные пользователя после успешной проверки логина и пароля."""

    username: str
    full_name: str
    role: str
    source: str
    groups: list[str]


class AuthProvider(Protocol):
    """Общий контракт для всех способов аутентификации."""

    async def authenticate(
        self,
        session: AsyncSession,
        username: str,
        password: str,
    ) -> AuthenticatedIdentity | None:
        """Проверяет учётные данные и возвращает данные пользователя при успехе."""


class LocalAuthProvider:
    """Локальная аутентификация по пользователям в БД."""

    async def authenticate(
        self,
        session: AsyncSession,
        username: str,
        password: str,
    ) -> AuthenticatedIdentity | None:
        """Проверяет логин и пароль по локальной таблице пользователей."""
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        if not user.is_active:
            return None
        if not _password_hasher.verify(password, user.password_hash):
            return None

        return AuthenticatedIdentity(
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            source="local",
            groups=[],
        )


class LDAPAuthProvider:
    """Аутентификация через LDAP с определением роли по группам."""

    async def authenticate(
        self,
        session: AsyncSession,  # noqa: ARG002
        username: str,
        password: str,
    ) -> AuthenticatedIdentity | None:
        """Проверяет учётные данные через LDAP и извлекает роль из групп."""
        del session
        if not settings.ldap_server_url or not settings.ldap_base_dn:
            logger.warning(
                "LDAP provider пропущен: отсутствует ldap_server_url или ldap_base_dn"
            )
            return None

        try:
            from ldap3 import ALL, Connection, Server, Tls  # type: ignore[import-untyped]
        except ImportError:
            logger.exception("LDAP provider недоступен: пакет ldap3 не установлен")
            return None

        tls_config = None
        if settings.ldap_use_tls:
            validate_mode = (
                ssl.CERT_REQUIRED if settings.ldap_tls_validate else ssl.CERT_NONE
            )
            tls_config = Tls(validate=validate_mode)

        server = Server(
            settings.ldap_server_url,
            get_info=ALL,
            use_ssl=settings.ldap_use_tls,
            tls=tls_config,
        )
        bind_dn = settings.ldap_bind_dn_template.format(username=username)
        connection = Connection(
            server,
            user=bind_dn,
            password=password,
            auto_bind=False,
            raise_exceptions=False,
        )

        if not connection.bind():
            logger.warning("LDAP bind неуспешен для username=%s", username)
            return None

        filter_value = settings.ldap_user_filter.format(username=username)
        search_success = connection.search(
            search_base=settings.ldap_base_dn,
            search_filter=filter_value,
            attributes=["displayName", "memberOf"],
            size_limit=1,
        )
        if not search_success or not connection.entries:
            connection.unbind()
            logger.warning(
                "LDAP user не найден после успешного bind: username=%s", username
            )
            return None

        entry = connection.entries[0]
        groups = _extract_groups(entry)
        resolved_role = resolve_role_from_ldap_groups(
            groups, settings.ldap_group_role_map, settings.ldap_default_role
        )
        full_name = _extract_full_name(entry, username)
        connection.unbind()

        return AuthenticatedIdentity(
            username=username,
            full_name=full_name,
            role=resolved_role,
            source="ldap",
            groups=groups,
        )


def build_auth_provider() -> AuthProvider:
    """Возвращает способ аутентификации, выбранный в настройках."""
    if settings.auth_provider == "ldap":
        return LDAPAuthProvider()
    return LocalAuthProvider()


def parse_ldap_group_role_map(raw_mapping: str) -> dict[str, str]:
    """Разбирает строку сопоставления LDAP-групп и ролей приложения.

    Формат:
    group_dn_1:role_1;group_dn_2:role_2
    """
    if not raw_mapping.strip():
        return {}

    mapping: dict[str, str] = {}
    chunks = [chunk.strip() for chunk in raw_mapping.split(";") if chunk.strip()]
    for chunk in chunks:
        if ":" not in chunk:
            continue
        group_name, role_name = chunk.split(":", maxsplit=1)
        group_key = group_name.strip().lower()
        role_value = role_name.strip()
        if not group_key:
            continue
        if role_value not in {role.value for role in UserRole}:
            continue
        mapping[group_key] = role_value
    return mapping


def resolve_role_from_ldap_groups(
    groups: list[str], raw_mapping: str, default_role: str
) -> str:
    """Определяет роль пользователя на основе LDAP групп.

    Если нет совпадений по маппингу — используется default_role.
    """
    mapping = parse_ldap_group_role_map(raw_mapping)
    for group in groups:
        normalized_group = group.strip().lower()
        if normalized_group in mapping:
            return mapping[normalized_group]

    if default_role in {role.value for role in UserRole}:
        return default_role
    return UserRole.EMPLOYEE.value


def _extract_groups(entry: object) -> list[str]:
    """Извлекает список LDAP-групп из ответа каталога в безопасном виде."""
    if not hasattr(entry, "memberOf"):
        return []
    values = getattr(entry.memberOf, "values", None)
    if values is None:
        raw_value = getattr(entry.memberOf, "value", None)
        if raw_value is None:
            return []
        return [str(raw_value)]
    return [str(value) for value in values]


def _extract_full_name(entry: object, fallback_username: str) -> str:
    """Возвращает ФИО из LDAP или логин, если ФИО не заполнено."""
    if not hasattr(entry, "displayName"):
        return fallback_username
    value = getattr(entry.displayName, "value", None)
    if value is None:
        return fallback_username
    normalized_value = str(value).strip()
    return normalized_value if normalized_value else fallback_username
