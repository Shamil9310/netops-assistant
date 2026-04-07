from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PlannedEventType(StrEnum):
    """Типы плановых событий.

    Плановые события создаются заранее и могут быть автоматически включены
    в дневной отчёт, если наступили сегодня.
    """

    # Запланированный звонок с клиентом, вендором, коллегами.
    CALL = "call"
    # Встреча, совещание, синк.
    MEETING = "meeting"
    # Плановое техническое обслуживание или работы.
    MAINTENANCE = "maintenance"
    # Дедлайн задачи или заявки.
    DEADLINE = "deadline"
    # Произвольное событие.
    OTHER = "other"


class PlannedEvent(Base):
    """Плановое событие — будущая активность, запланированная заранее.

    Сотрудник создаёт плановые события для напоминания и включения в отчёты.
    Если событие наступает сегодня — оно автоматически появляется в дашборде дня.
    После выполнения событие помечается как completed.
    """

    __tablename__ = "planned_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Владелец события — видит и редактирует только свои события.
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Привязка к внешней заявке/SR — для связи с ITSM.
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # Время планируемого начала — ключевое поле для фильтрации по дате.
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Флаг выполнения — заменяет сложный статусный lifecycle для простых событий.
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # Если событие включено в дневной журнал — ссылка на соответствующую запись.
    # Позволяет избежать дублирования данных при авто-включении в отчёт.
    linked_journal_entry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("activity_entries.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", lazy="selectin")
