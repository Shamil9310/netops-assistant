from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkTimerTaskStatus(StrEnum):
    """Статусы рабочей задачи в таймере."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class WorkTimerSessionStatus(StrEnum):
    """Статусы таймерной сессии."""

    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class WorkTimerTask(Base):
    """Рабочая задача, к которой привязываются таймерные сессии."""

    __tablename__ = "work_timer_tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_ref: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    task_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    tags: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=WorkTimerTaskStatus.TODO.value,
        server_default=WorkTimerTaskStatus.TODO.value,
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    sessions: Mapped[list[WorkTimerSession]] = relationship(
        "WorkTimerSession",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="WorkTimerSession.started_at",
        lazy="selectin",
    )
    user = relationship("User", lazy="selectin")


class WorkTimerSession(Base):
    """Одна таймерная сессия для конкретной задачи."""

    __tablename__ = "work_timer_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("work_timer_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=WorkTimerSessionStatus.RUNNING.value,
        server_default=WorkTimerSessionStatus.RUNNING.value,
        index=True,
    )
    tags_snapshot: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
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

    task: Mapped[WorkTimerTask] = relationship(
        "WorkTimerTask", back_populates="sessions"
    )
    interruptions: Mapped[list[WorkTimerInterruption]] = relationship(
        "WorkTimerInterruption",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="WorkTimerInterruption.started_at",
        lazy="selectin",
    )
    user = relationship("User", lazy="selectin")


class WorkTimerInterruption(Base):
    """Запись о прерывании таймерной сессии."""

    __tablename__ = "work_timer_interruptions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("work_timer_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
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

    session: Mapped[WorkTimerSession] = relationship(
        "WorkTimerSession", back_populates="interruptions"
    )
