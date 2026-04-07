from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access_audit import AccessAuditEvent


async def log_access_event(
    session: AsyncSession,
    user_id: UUID,
    resource_type: str,
    resource_id: str,
    action: str,
    request_id: str | None,
    target_user_id: UUID | None = None,
) -> None:
    """Сохраняет аудит-событие доступа к данным или экспорту."""
    session.add(
        AccessAuditEvent(
            user_id=user_id,
            target_user_id=target_user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            request_id=request_id,
        )
    )
    await session.commit()
