"""Тесты иерархии исключений приложения.

Проверяем, что:
- каждый тип исключения является подклассом AppError;
- строковое представление содержит переданное сообщение;
- исключения перехватываются через базовый класс;
- исключения перехватываются через стандартный Exception.
"""

from __future__ import annotations

import pytest

from app.core.exceptions import (
    AccessDeniedError,
    AppError,
    BusinessError,
    NotFoundError,
    UserError,
)


def test_user_error_is_subclass_of_app_error() -> None:
    """UserError должен наследоваться от AppError."""
    assert issubclass(UserError, AppError)


def test_business_error_is_subclass_of_app_error() -> None:
    """BusinessError должен наследоваться от AppError."""
    assert issubclass(BusinessError, AppError)


def test_not_found_error_is_subclass_of_app_error() -> None:
    """NotFoundError должен наследоваться от AppError."""
    assert issubclass(NotFoundError, AppError)


def test_access_denied_error_is_subclass_of_app_error() -> None:
    """AccessDeniedError должен наследоваться от AppError."""
    assert issubclass(AccessDeniedError, AppError)


def test_all_errors_are_subclass_of_exception() -> None:
    """Все кастомные исключения должны наследоваться от Exception."""
    for cls in (AppError, UserError, BusinessError, NotFoundError, AccessDeniedError):
        assert issubclass(cls, Exception)


def test_message_is_preserved_in_user_error() -> None:
    """Сообщение должно сохраняться в атрибуте message и str()."""
    msg = "Время окончания не может быть раньше времени начала"
    exc = UserError(msg)
    assert exc.message == msg
    assert str(exc) == msg


def test_message_is_preserved_in_business_error() -> None:
    """Сообщение должно сохраняться в BusinessError."""
    msg = "Таймер уже запущен"
    exc = BusinessError(msg)
    assert exc.message == msg
    assert str(exc) == msg


def test_message_is_preserved_in_not_found_error() -> None:
    """Сообщение должно сохраняться в NotFoundError."""
    msg = "Запись не найдена"
    exc = NotFoundError(msg)
    assert exc.message == msg
    assert str(exc) == msg


def test_message_is_preserved_in_access_denied_error() -> None:
    """Сообщение должно сохраняться в AccessDeniedError."""
    msg = "Доступ запрещён"
    exc = AccessDeniedError(msg)
    assert exc.message == msg
    assert str(exc) == msg


def test_user_error_caught_as_app_error() -> None:
    """UserError должен перехватываться через AppError."""
    with pytest.raises(AppError):
        raise UserError("ошибка ввода")


def test_business_error_caught_as_app_error() -> None:
    """BusinessError должен перехватываться через AppError."""
    with pytest.raises(AppError):
        raise BusinessError("конфликт состояния")


def test_not_found_error_caught_as_app_error() -> None:
    """NotFoundError должен перехватываться через AppError."""
    with pytest.raises(AppError):
        raise NotFoundError("объект не найден")


def test_access_denied_error_caught_as_app_error() -> None:
    """AccessDeniedError должен перехватываться через AppError."""
    with pytest.raises(AppError):
        raise AccessDeniedError("нет прав")


def test_exceptions_are_distinct_types() -> None:
    """Разные типы исключений не должны перехватываться как один и тот же тип."""
    with pytest.raises(UserError):
        raise UserError("только UserError")

    # BusinessError не должен быть перехвачен как UserError.
    with pytest.raises(BusinessError):
        raise BusinessError("только BusinessError")
