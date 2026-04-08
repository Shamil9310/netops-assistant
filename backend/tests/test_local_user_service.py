"""Тесты управления локальными пользователями через auth-сервис."""

from __future__ import annotations

import pytest
from uuid import uuid4

from app.models.user import UserRole
from app.services.auth import (
    LocalUserCreateError,
    create_local_user,
    delete_local_user,
    verify_password,
)


class _QueryResultStub:
    def __init__(self, user: object | None) -> None:
        self._user = user

    def scalar_one_or_none(self) -> object | None:
        return self._user


class _SessionStub:
    def __init__(self, existing_user: object | None = None) -> None:
        self.existing_user = existing_user
        self.added_user = None
        self.committed = False
        self.refreshed = False
        self.deleted_user = None

    async def execute(self, _statement: object) -> _QueryResultStub:
        return _QueryResultStub(self.existing_user)

    async def get(self, _model: object, _user_id: object) -> object | None:
        return self.existing_user

    def add(self, user: object) -> None:
        self.added_user = user

    async def delete(self, user: object) -> None:
        self.deleted_user = user

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, _obj: object) -> None:
        self.refreshed = True

    async def rollback(self) -> None:
        return None


@pytest.mark.asyncio
async def test_create_local_user_creates_account() -> None:
    session = _SessionStub()

    creation_result = await create_local_user(
        session,
        username="employee-1",
        full_name="Employee One",
        password="StrongPass123",
        role=UserRole.EMPLOYEE.value,
        is_active=True,
    )
    user = creation_result.user

    assert session.added_user is user
    assert session.committed is True
    assert session.refreshed is True
    assert creation_result.generated_password is None
    assert user.username == "employee-1"
    assert user.full_name == "Employee One"
    assert user.role == UserRole.EMPLOYEE.value
    assert user.is_active is True
    assert user.password_hash != "StrongPass123"
    assert verify_password("StrongPass123", user.password_hash) is True


@pytest.mark.asyncio
async def test_create_local_user_rejects_duplicate_username() -> None:
    session = _SessionStub(existing_user=object())

    try:
        await create_local_user(
            session,
            username="manager-1",
            full_name="Manager One",
            password="StrongPass123",
            role=UserRole.MANAGER.value,
            is_active=True,
        )
        raise AssertionError("Expected LocalUserCreateError for duplicate username")
    except LocalUserCreateError as exc:
        assert exc.status_code == 409


@pytest.mark.asyncio
async def test_create_local_user_rejects_invalid_role() -> None:
    session = _SessionStub()

    try:
        await create_local_user(
            session,
            username="bad-role-user",
            full_name="Bad Role User",
            password="StrongPass123",
            role="superadmin",
            is_active=True,
        )
        raise AssertionError("Expected LocalUserCreateError for invalid role")
    except LocalUserCreateError as exc:
        assert exc.status_code == 400


@pytest.mark.asyncio
async def test_create_local_user_trims_username_and_full_name() -> None:
    session = _SessionStub()

    creation_result = await create_local_user(
        session,
        username="  manager-1  ",
        full_name="  Manager One  ",
        password="StrongPass123",
        role="MANAGER",
        is_active=True,
    )
    user = creation_result.user

    assert user.username == "manager-1"
    assert user.full_name == "Manager One"
    assert user.role == UserRole.MANAGER.value


@pytest.mark.asyncio
async def test_create_local_user_rejects_short_username_after_trim() -> None:
    session = _SessionStub()

    try:
        await create_local_user(
            session,
            username="  a ",
            full_name="Valid Full Name",
            password="StrongPass123",
            role=UserRole.EMPLOYEE.value,
            is_active=True,
        )
        raise AssertionError("Expected LocalUserCreateError for short username")
    except LocalUserCreateError as exc:
        assert exc.status_code == 400
        assert "Логин" in exc.detail


@pytest.mark.asyncio
async def test_create_local_user_rejects_short_full_name_after_trim() -> None:
    session = _SessionStub()

    try:
        await create_local_user(
            session,
            username="valid-user",
            full_name=" a ",
            password="StrongPass123",
            role=UserRole.EMPLOYEE.value,
            is_active=True,
        )
        raise AssertionError("Expected LocalUserCreateError for short full_name")
    except LocalUserCreateError as exc:
        assert exc.status_code == 400
        assert "ФИО" in exc.detail


@pytest.mark.asyncio
async def test_create_local_user_rejects_short_password_after_trim() -> None:
    session = _SessionStub()

    try:
        await create_local_user(
            session,
            username="valid-user",
            full_name="Valid Full Name",
            password="   1234567   ",
            role=UserRole.EMPLOYEE.value,
            is_active=True,
        )
        raise AssertionError("Expected LocalUserCreateError for short password")
    except LocalUserCreateError as exc:
        assert exc.status_code == 400
        assert "Пароль" in exc.detail


@pytest.mark.asyncio
async def test_create_local_user_generates_password_when_missing() -> None:
    session = _SessionStub()

    creation_result = await create_local_user(
        session,
        username="generated-user",
        full_name="Generated User",
        password=None,
        role=UserRole.EMPLOYEE.value,
        is_active=True,
    )

    assert creation_result.generated_password is not None
    assert len(creation_result.generated_password) >= 8
    assert (
        verify_password(
            creation_result.generated_password, creation_result.user.password_hash
        )
        is True
    )


@pytest.mark.asyncio
async def test_delete_local_user_removes_account() -> None:
    user = type("UserStub", (), {"id": uuid4(), "username": "delete-me"})()
    session = _SessionStub(existing_user=user)

    deleted = await delete_local_user(session, user.id, uuid4())

    assert deleted is user
    assert session.deleted_user is user
    assert session.committed is True


@pytest.mark.asyncio
async def test_delete_local_user_rejects_self_deletion() -> None:
    user_id = uuid4()
    user = type("UserStub", (), {"id": user_id, "username": "self"})()
    session = _SessionStub(existing_user=user)

    with pytest.raises(LocalUserCreateError) as exc_info:
        await delete_local_user(session, user_id, user_id)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_delete_local_user_returns_404_when_user_missing() -> None:
    session = _SessionStub(existing_user=None)

    with pytest.raises(LocalUserCreateError) as exc_info:
        await delete_local_user(session, uuid4(), uuid4())

    assert exc_info.value.status_code == 404
