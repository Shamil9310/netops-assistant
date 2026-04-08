from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, model_validator


ActivityType = Literal[
    "call",
    "ticket",
    "meeting",
    "task",
    "escalation",
    "other",
]
ActivityStatus = Literal["open", "in_progress", "closed", "cancelled"]


class ActivityEntryCreateRequest(BaseModel):
    """Входная схема создания записи журнала.

    Важный бизнес-смысл:
    work_date — это дата, за которую запись должна попасть в отчёт.
    Именно её пользователь может указывать вручную, включая:
    - прошлые даты;
    - текущую дату;
    - будущие даты.
    """

    work_date: date
    activity_type: ActivityType
    status: ActivityStatus = "open"
    title: str = Field(min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    resolution: str | None = Field(default=None, max_length=5000)
    contact: str | None = Field(default=None, max_length=256)
    ticket_number: str | None = Field(default=None, max_length=64)
    task_url: str | None = Field(default=None, max_length=2048)
    started_at: time | None = None
    ended_at: time | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "ActivityEntryCreateRequest":
        """Проверяет корректность временного диапазона.

        Бизнес-правило простое:
        если указано и начало, и окончание, окончание не может быть раньше начала.
        """
        if self.started_at and self.ended_at and self.ended_at < self.started_at:
            raise ValueError("Время окончания не может быть раньше начала")

        return self


class ActivityEntryUpdateRequest(BaseModel):
    """Схема частичного обновления записи журнала."""

    work_date: date | None = None
    activity_type: ActivityType | None = None
    status: ActivityStatus | None = None
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    resolution: str | None = Field(default=None, max_length=5000)
    contact: str | None = Field(default=None, max_length=256)
    ticket_number: str | None = Field(default=None, max_length=64)
    task_url: str | None = Field(default=None, max_length=2048)
    started_at: time | None = None
    ended_at: time | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "ActivityEntryUpdateRequest":
        """Проверяет корректность времени, если переданы оба поля."""
        if self.started_at and self.ended_at and self.ended_at < self.started_at:
            raise ValueError("Время окончания не может быть раньше времени начала")
        return self


class ActivityEntryResponse(BaseModel):
    """Схема ответа с записью журнала."""

    id: str
    user_id: str
    work_date: date
    activity_type: ActivityType
    status: ActivityStatus
    title: str
    description: str | None
    resolution: str | None
    contact: str | None
    ticket_number: str | None
    task_url: str | None
    started_at: time | None
    ended_at: time | None
    is_backdated: bool
    created_at: datetime
    updated_at: datetime


class ActivityEntryListResponse(BaseModel):
    """Список записей за выбранную рабочую дату."""

    work_date: date
    total: int
    items: list[ActivityEntryResponse]
