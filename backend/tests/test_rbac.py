"""Тесты для RBAC: роли пользователей и permission policies."""

from __future__ import annotations


from app.models.user import UserRole


def test_user_role_values_are_stable() -> None:
    """Значения ролей не должны меняться — они хранятся в БД как строки."""
    assert UserRole.EMPLOYEE.value == "employee"
    assert UserRole.MANAGER.value == "manager"
    assert UserRole.DEVELOPER.value == "developer"


def test_all_roles_are_unique() -> None:
    """Все роли должны иметь уникальные строковые значения."""
    values = [r.value for r in UserRole]
    assert len(values) == len(set(values))


def test_role_iteration() -> None:
    """Перечисление ролей должно содержать ровно три роли."""
    roles = list(UserRole)
    assert len(roles) == 3


def test_valid_role_membership() -> None:
    """Строковые значения валидных ролей принадлежат перечислению."""
    valid_role_values = {r.value for r in UserRole}
    assert "employee" in valid_role_values
    assert "manager" in valid_role_values
    assert "developer" in valid_role_values


def test_invalid_role_not_in_enum() -> None:
    """Несуществующая роль не должна быть в перечислении."""
    valid_role_values = {r.value for r in UserRole}
    assert "admin" not in valid_role_values
    assert "superuser" not in valid_role_values
    assert "" not in valid_role_values
