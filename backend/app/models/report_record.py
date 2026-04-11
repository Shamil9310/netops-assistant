from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReportType(StrEnum):
    """Типы генерируемых отчётов."""

    DAILY = "daily"
    WEEKLY = "weekly"
    RANGE = "range"
    NIGHT_WORK_RESULT = "night_work_result"


class ReportStatus(StrEnum):
    """Статус жизненного цикла отчёта."""

    DRAFT = "draft"
    FINAL = "final"


class ReportRecord(Base):
    """История сгенерированных отчётов.

    Каждый раз при запросе отчёта через API мы сохраняем запись
    в историю — это позволяет повторно открыть или скачать отчёт
    без повторной генерации.
    """

    __tablename__ = "report_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    report_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    report_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ReportStatus.DRAFT.value,
        server_default=ReportStatus.DRAFT.value,
        index=True,
    )

    # Период отчёта в ISO-формате для показа в истории.
    period_from: Mapped[str] = mapped_column(String(10), nullable=False)
    period_to: Mapped[str] = mapped_column(String(10), nullable=False)

    # Готовое содержимое отчёта в формате Markdown.
    content_md: Mapped[str] = mapped_column(Text, nullable=False)

    # Сохраняем правила фильтрации услуг вместе с отчётом, чтобы refresh
    # и пересборка final -> draft воспроизводили тот же набор записей.
    service_filter_mode: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="all",
        server_default="all",
    )
    service_filters: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
