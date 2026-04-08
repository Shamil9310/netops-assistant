from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuthAuditEventType(StrEnum):
    """Типы событий аудита аутентификации.

    Журналируем ключевые события auth-слоя для безопасности и отладки:
    - LOGIN_SUCCESS / LOGIN_FAILED — попытки входа.
    - LOGOUT — явный выход пользователя.
    - SESSION_EXPIRED — сессия истекла по TTL (фиксируется при проверке).
    """

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    SESSION_EXPIRED = "session_expired"


class AuthAuditEvent(Base):
    """Таблица аудита auth-событий.

    Хранит историю входов, выходов и ошибок аутентификации.
    Не удаляем записи — это журнал безопасности.
    """

    __tablename__ = "auth_audit_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # user_id может быть пустым при неудачном входе, если такого пользователя не было.
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Имя пользователя сохраняем отдельно, потому что при неудачном входе user_id может быть пустым.
    username_attempted: Mapped[str] = mapped_column(String(64), nullable=False)

    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # IP-адрес клиента — полезен для анализа подозрительной активности.
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
