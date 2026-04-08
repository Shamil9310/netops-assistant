from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class DailyReportRequest(BaseModel):
    """Запрос на генерацию дневного отчёта."""

    report_date: date
    format_profile: str = "engineer"


class WeeklyReportRequest(BaseModel):
    """Запрос на генерацию недельного отчёта.

    Поле week_start должно указывать на понедельник нужной недели.
    """

    week_start: date
    format_profile: str = "engineer"


class RangeReportRequest(BaseModel):
    """Запрос на генерацию отчёта за произвольный период."""

    date_from: date
    date_to: date
    format_profile: str = "engineer"


class ReportPreviewResponse(BaseModel):
    """Предпросмотр отчёта — Markdown-контент и метаданные."""

    report_id: str
    report_type: str
    report_status: str
    period_from: str
    period_to: str
    content_md: str
    generated_at: datetime
    updates_after_finalization: int = 0


class ReportRecordResponse(BaseModel):
    """Запись в истории генераций."""

    id: str
    report_type: str
    report_status: str
    period_from: str
    period_to: str
    generated_at: datetime
