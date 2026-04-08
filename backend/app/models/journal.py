from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ActivityType(StrEnum):
    """Типы активности в журнале дневных операций.

    Классифицируем события по характеру работы — это позволяет
    строить отчёты по категориям и анализировать нагрузку.
    """

    # Входящий или исходящий звонок.
    CALL = "call"
    # Работа с заявкой (SR, incident, task).
    TICKET = "ticket"
    # Встреча, совещание, планёрка.
    MEETING = "meeting"
    # Выполнение плановой или внеплановой задачи.
    TASK = "task"
    # Эскалация, передача задачи другому сотруднику или уровню поддержки.
    ESCALATION = "escalation"
    # Произвольное событие, не подходящее ни в одну категорию.
    OTHER = "other"


class ActivityStatus(StrEnum):
    """Статус записи журнала.

    Отражает жизненный цикл активности:
    открыта → в работе → закрыта / отменена.
    """

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ActivityEntry(Base):
    """Запись журнала дневной операционной активности.

    Центральная сущность дневного контура (day ops).
    Каждый сотрудник фиксирует свои активности — звонки, заявки, встречи.
    На основе этих записей строятся отчёты и дашборд текущего дня.
    """

    __tablename__ = "activity_entries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Автор записи — только владелец может редактировать/удалять.
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Рабочая дата записи: именно по ней строятся дневные и периодные отчёты.
    work_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    activity_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ActivityStatus.OPEN.value,
        server_default=ActivityStatus.OPEN.value,
        index=True,
    )

    # Заголовок — краткое описание, видно в списке журнала.
    title: Mapped[str] = mapped_column(String(256), nullable=False)

    # Описание — детали, действия, результаты. Опционально.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Что было сделано для решения задачи.
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    # От кого пришла задача: имя, отдел, email, телефон.
    contact: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Номер заявки/SR/тикета во внешней системе — для привязки к ITSM.
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    # Явное поле тикета для нового контракта journal API.
    # На этапе миграции поддерживаем оба поля: ticket_number и external_ref.
    ticket_number: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    # Ссылка на карточку задачи во внешней системе, например в BPM.
    task_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Время фактического начала активности (может отличаться от created_at).
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Время фактического завершения активности.
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

    user = relationship("User", lazy="selectin")
