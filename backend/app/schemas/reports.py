from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ServiceFilterMode = Literal["all", "include", "exclude", "empty"]


class ReportServiceFilterMixin(BaseModel):
    """Общие поля фильтрации услуг для генерации отчётов."""

    service_filter_mode: ServiceFilterMode = "all"
    service_filters: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def normalize_service_filters(self):
        """Нормализует список услуг и очищает лишние значения для простых режимов."""
        normalized_filters: list[str] = []
        seen_filters: set[str] = set()

        for raw_service in self.service_filters:
            normalized_service = raw_service.strip()
            if not normalized_service or normalized_service in seen_filters:
                continue
            normalized_filters.append(normalized_service)
            seen_filters.add(normalized_service)

        self.service_filters = normalized_filters

        if self.service_filter_mode in {"all", "empty"}:
            self.service_filters = []

        return self


class DailyReportRequest(ReportServiceFilterMixin):
    """Запрос на генерацию дневного отчёта."""

    report_date: date
    format_profile: str = "engineer"


class WeeklyReportRequest(ReportServiceFilterMixin):
    """Запрос на генерацию недельного отчёта.

    Поле week_start должно указывать на понедельник нужной недели.
    """

    week_start: date
    format_profile: str = "engineer"


class RangeReportRequest(ReportServiceFilterMixin):
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
