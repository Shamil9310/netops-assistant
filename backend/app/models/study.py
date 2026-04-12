from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StudyPlanStatus(StrEnum):
    """Статусы учебного плана."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StudyPlanTrack(StrEnum):
    """Направления учебного плана."""

    PYTHON = "python"
    NETWORKS = "networks"


class StudySessionStatus(StrEnum):
    """Статусы таймерной сессии учёбы."""

    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class StudyPlan(Base):
    """Учебный план с модулями, чекпоинтами, чеклистом и историей таймера."""

    __tablename__ = "study_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    track: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=StudyPlanTrack.PYTHON.value,
        server_default=StudyPlanTrack.PYTHON.value,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=StudyPlanStatus.DRAFT.value,
        server_default=StudyPlanStatus.DRAFT.value,
        index=True,
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

    modules: Mapped[list[StudyModule]] = relationship(
        "StudyModule",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="StudyModule.order_index",
        lazy="selectin",
    )
    checkpoints: Mapped[list[StudyCheckpoint]] = relationship(
        "StudyCheckpoint",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="StudyCheckpoint.order_index",
        lazy="selectin",
    )
    checklist_items: Mapped[list[StudyChecklistItem]] = relationship(
        "StudyChecklistItem",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="StudyChecklistItem.order_index",
        lazy="selectin",
    )
    sessions: Mapped[list[StudySession]] = relationship(
        "StudySession",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="StudySession.started_at",
        lazy="selectin",
    )
    user = relationship("User", lazy="selectin")


class StudyModule(Base):
    """Блок (модуль) учебного плана — группирует темы по разделам."""

    __tablename__ = "study_modules"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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

    plan: Mapped[StudyPlan] = relationship("StudyPlan", back_populates="modules")
    checkpoints: Mapped[list[StudyCheckpoint]] = relationship(
        "StudyCheckpoint",
        back_populates="module",
        order_by="StudyCheckpoint.order_index",
        lazy="selectin",
    )


class StudyCheckpoint(Base):
    """Этап или чекпоинт учебного плана."""

    __tablename__ = "study_checkpoints"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("study_modules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_percent: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    is_done: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
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

    plan: Mapped[StudyPlan] = relationship("StudyPlan", back_populates="checkpoints")
    module: Mapped[StudyModule | None] = relationship(
        "StudyModule", back_populates="checkpoints"
    )
    checklist_items: Mapped[list[StudyChecklistItem]] = relationship(
        "StudyChecklistItem",
        back_populates="checkpoint",
        lazy="selectin",
    )


class StudyChecklistItem(Base):
    """Пункт чеклиста внутри учебного плана."""

    __tablename__ = "study_checklist_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    checkpoint_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("study_checkpoints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_done: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
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

    plan: Mapped[StudyPlan] = relationship(
        "StudyPlan", back_populates="checklist_items"
    )
    checkpoint: Mapped[StudyCheckpoint | None] = relationship(
        "StudyCheckpoint", back_populates="checklist_items"
    )


class StudySession(Base):
    """Таймерная сессия учёбы."""

    __tablename__ = "study_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    checkpoint_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("study_checkpoints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=StudySessionStatus.RUNNING.value,
        server_default=StudySessionStatus.RUNNING.value,
        index=True,
    )
    progress_percent: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
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

    plan: Mapped[StudyPlan] = relationship("StudyPlan", back_populates="sessions")
    checkpoint: Mapped[StudyCheckpoint | None] = relationship("StudyCheckpoint")
