"""Тесты слоя аутентификации и сопоставления LDAP-групп с ролями приложения."""

from __future__ import annotations

from app.models.user import UserRole
from app.services.auth_provider import (
    parse_ldap_group_role_map,
    resolve_role_from_ldap_groups,
)


def test_parse_ldap_group_role_map_happy_path() -> None:
    """Проверяет корректный разбор строки сопоставления LDAP-групп и ролей."""
    raw = "cn=netops-managers,ou=groups,dc=corp,dc=local:manager; cn=netops-dev,ou=groups,dc=corp,dc=local:developer"
    parsed = parse_ldap_group_role_map(raw)
    assert (
        parsed["cn=netops-managers,ou=groups,dc=corp,dc=local"]
        == UserRole.MANAGER.value
    )
    assert (
        parsed["cn=netops-dev,ou=groups,dc=corp,dc=local"] == UserRole.DEVELOPER.value
    )


def test_parse_ldap_group_role_map_ignores_invalid_role() -> None:
    """Некорректные роли в маппинге игнорируются, чтобы не ломать вход пользователя."""
    raw = "cn=netops-bad,ou=groups,dc=corp,dc=local:superadmin"
    parsed = parse_ldap_group_role_map(raw)
    assert parsed == {}


def test_resolve_role_from_ldap_groups_happy_path() -> None:
    """Если группа найдена в маппинге, пользователь получает соответствующую роль."""
    groups = [
        "CN=NetOps-Employees,OU=Groups,DC=corp,DC=local",
        "CN=NetOps-Managers,OU=Groups,DC=corp,DC=local",
    ]
    mapping = "cn=netops-managers,ou=groups,dc=corp,dc=local:manager"
    role = resolve_role_from_ldap_groups(groups, mapping, default_role="employee")
    assert role == UserRole.MANAGER.value


def test_resolve_role_from_ldap_groups_fallback_to_default() -> None:
    """Если совпадений нет, возвращается безопасная роль по умолчанию."""
    groups = ["CN=Unknown,OU=Groups,DC=corp,DC=local"]
    role = resolve_role_from_ldap_groups(groups, "", default_role="employee")
    assert role == UserRole.EMPLOYEE.value


def test_resolve_role_from_ldap_groups_invalid_default() -> None:
    """Некорректная роль по умолчанию заменяется на employee с минимальными правами."""
    groups = []
    role = resolve_role_from_ldap_groups(groups, "", default_role="superadmin")
    assert role == UserRole.EMPLOYEE.value
