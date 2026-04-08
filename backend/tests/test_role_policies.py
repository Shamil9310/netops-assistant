"""Придирчивые тесты RBAC dependency-политик."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.deps import require_developer, require_manager


@pytest.mark.asyncio
async def test_require_manager_allows_manager() -> None:
    user = SimpleNamespace(role="manager")
    resolved = await require_manager(user)  # type: ignore[arg-type]
    assert resolved is user


@pytest.mark.asyncio
async def test_require_manager_allows_developer() -> None:
    user = SimpleNamespace(role="developer")
    resolved = await require_manager(user)  # type: ignore[arg-type]
    assert resolved is user


@pytest.mark.asyncio
async def test_require_manager_denies_employee() -> None:
    user = SimpleNamespace(role="employee")
    with pytest.raises(HTTPException) as exc_info:
        await require_manager(user)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 403
    assert "Доступ запрещён" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_require_developer_denies_manager() -> None:
    user = SimpleNamespace(role="manager")
    with pytest.raises(HTTPException) as exc_info:
        await require_developer(user)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_developer_allows_developer() -> None:
    user = SimpleNamespace(role="developer")
    resolved = await require_developer(user)  # type: ignore[arg-type]
    assert resolved is user
