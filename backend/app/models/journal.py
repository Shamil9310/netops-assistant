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
    # Работа с заявкой или обращением во внешней системе.
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

    Это основная сущность рабочего журнала.
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
    # Рабочая дата записи.
    # Именно по этой дате запись попадает в дневные и периодные отчёты.
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
    # От кого пришла задача: имя, отдел, электронная почта, телефон.
    contact: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # Название услуги или сервиса, с которым связана запись.
    service: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)

    # Номер заявки или SR во внешней системе.
    # Нужен, чтобы связать запись журнала с внешним процессом или обращением.
    external_ref: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    # Отдельное поле номера заявки нужно для текущего контракта API журнала.
    # Пока поддерживаем и его, и external_ref, чтобы не ломать старые данные.
    ticket_number: Mapped[str | None] = mapped_column(
        String(128), nullable=True, index=True
    )
    # Ссылка на карточку задачи во внешней системе или в рабочем источнике.
    task_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    # Фактическое время начала работы.
    # Может отличаться от времени создания записи в базе.
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Фактические дата и время завершения работы.
    # Может быть позже рабочей даты, если задача закрыта на следующий день.
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    user = relationship("User", lazy="selectin")
