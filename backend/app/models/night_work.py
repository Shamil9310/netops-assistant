from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NightWorkPlanStatus(StrEnum):
    """Статус плана ночных работ.

    Жизненный цикл плана:
    DRAFT → APPROVED → IN_PROGRESS → COMPLETED / CANCELLED
    DRAFT — редактируется, ещё не утверждён.
    APPROVED — утверждён, готов к исполнению.
    IN_PROGRESS — исполняется прямо сейчас (ночная смена).
    COMPLETED — все блоки выполнены.
    CANCELLED — план отменён (например, отложены работы).
    """

    DRAFT = "draft"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NightWorkBlockStatus(StrEnum):
    """Статус блока (SR / изменения) внутри плана.

    PENDING — ожидает исполнения.
    IN_PROGRESS — исполняется.
    COMPLETED — успешно выполнен.
    FAILED — завершён с ошибкой.
    SKIPPED — пропущен (например, по согласованию).
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class NightWorkStepStatus(StrEnum):
    """Статус отдельного шага внутри блока.

    Аналогичен блоку, но на уровне конкретного действия.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class NightWorkPlan(Base):
    """План ночных работ — верхнеуровневый контейнер для набора изменений.

    Одна ночь = один план. Содержит несколько блоков (SR/изменений),
    каждый из которых состоит из шагов.
    """

    __tablename__ = "night_work_plans"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Автор и исполнитель плана.
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=NightWorkPlanStatus.DRAFT.value,
        server_default=NightWorkPlanStatus.DRAFT.value,
        index=True,
    )

    # Плановое время начала ночных работ.
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Участники окна (ФИО/логины коллег, участвующих в работах).
    participants: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")

    # Фактическое время начала и завершения.
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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

    blocks: Mapped[list[NightWorkBlock]] = relationship(
        "NightWorkBlock",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="NightWorkBlock.order_index",
        lazy="selectin",
    )
    user = relationship("User", lazy="selectin")


class NightWorkBlock(Base):
    """Блок плана ночных работ — один SR или одно изменение.

    Блок объединяет связанные шаги (проверки, команды, post-actions)
    для одного конкретного изменения в рамках ночи.
    """

    __tablename__ = "night_work_blocks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("night_work_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Номер SR или внешний идентификатор изменения.
    sr_number: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=NightWorkBlockStatus.PENDING.value,
        server_default=NightWorkBlockStatus.PENDING.value,
    )

    # Порядок исполнения блоков внутри плана.
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Комментарий исполнителя по результатам блока.
    result_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    plan: Mapped[NightWorkPlan] = relationship("NightWorkPlan", back_populates="blocks")
    steps: Mapped[list[NightWorkStep]] = relationship(
        "NightWorkStep",
        back_populates="block",
        cascade="all, delete-orphan",
        order_by="NightWorkStep.order_index",
        lazy="selectin",
    )


class NightWorkStep(Base):
    """Шаг внутри блока плана ночных работ.

    Шаг — атомарное действие: команда, проверка, откат, post-action.
    Каждый шаг фиксирует фактический результат при исполнении.
    """

    __tablename__ = "night_work_steps"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    block_id: Mapped[UUID] = mapped_column(
        ForeignKey("night_work_blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False)

    # Детали шага: команда, URL, описание проверки.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=NightWorkStepStatus.PENDING.value,
        server_default=NightWorkStepStatus.PENDING.value,
    )

    # Порядок исполнения шагов внутри блока.
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Флаг: является ли этот шаг rollback-действием.
    is_rollback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # Флаг: является ли этот шаг post-action (проверка после основного изменения).
    is_post_action: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # Фактический результат шага — заполняется при исполнении.
    actual_result: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Комментарий исполнителя (ошибки, отклонения от плана).
    executor_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    # С кем выполнялся шаг (для передачи контекста смен и кросс-командной работы).
    collaborators: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    # Куда передан шаг/проблема (смежная команда), если выполнение делегировано.
    handoff_to: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Фактическое время начала и завершения шага.
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    block: Mapped[NightWorkBlock] = relationship("NightWorkBlock", back_populates="steps")
