from __future__ import annotations

from datetime import datetime, date
from typing import Literal

from pydantic import BaseModel, Field

from app.models.work_timer import WorkTimerSessionStatus, WorkTimerTaskStatus


class WorkTimerInterruptionResponse(BaseModel):
    """Представление прерывания таймерной сессии."""

    id: str
    session_id: str
    reason: str | None
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    created_at: datetime
    updated_at: datetime


class WorkTimerSessionResponse(BaseModel):
    """Представление таймерной сессии."""

    id: str
    task_id: str
    status: WorkTimerSessionStatus
    tags_snapshot: list[str]
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    interruption_seconds: int
    interruptions_count: int
    created_at: datetime
    updated_at: datetime
    interruptions: list[WorkTimerInterruptionResponse]


class WorkTimerTaskResponse(BaseModel):
    """Представление рабочей задачи таймера."""

    id: str
    user_id: str
    title: str
    description: str | None
    task_ref: str | None
    task_url: str | None
    tags: list[str]
    order_index: int
    status: WorkTimerTaskStatus
    completed_at: datetime | None
    total_seconds: int
    interruption_seconds: int
    interruptions_count: int
    active_session_id: str | None
    active_session_started_at: datetime | None
    created_at: datetime
    updated_at: datetime
    sessions: list[WorkTimerSessionResponse]


class WorkTimerTaskCreateRequest(BaseModel):
    """Запрос на создание задачи таймера."""

    title: str = Field(min_length=2, max_length=256)
    description: str | None = None
    task_ref: str | None = Field(default=None, max_length=128)
    task_url: str | None = Field(default=None, max_length=2048)
    tags: list[str] = Field(default_factory=list)
    order_index: int = Field(default=0, ge=0)
    status: WorkTimerTaskStatus = WorkTimerTaskStatus.TODO


class WorkTimerTaskUpdateRequest(BaseModel):
    """Запрос на обновление задачи таймера."""

    title: str | None = Field(default=None, min_length=2, max_length=256)
    description: str | None = None
    task_ref: str | None = Field(default=None, max_length=128)
    task_url: str | None = Field(default=None, max_length=2048)
    tags: list[str] | None = None
    order_index: int | None = Field(default=None, ge=0)
    status: WorkTimerTaskStatus | None = None
    completed_at: datetime | None = None


class WorkTimerTimerActionRequest(BaseModel):
    """Запрос на действие с таймером."""

    action: Literal["start", "pause", "resume", "stop"]
    interruption_reason: str | None = Field(default=None, max_length=2000)


class WorkTimerDaySummary(BaseModel):
    """Сводка по одному дню недели."""

    day: date
    total_seconds: int
    sessions_count: int
    interruptions_count: int


class WorkTimerTaskSummary(BaseModel):
    """Сводка по задаче за неделю."""

    task_id: str
    title: str
    total_seconds: int
    sessions_count: int
    interruptions_count: int
    tags: list[str]


class WorkTimerTagSummary(BaseModel):
    """Сводка по тегу за неделю."""

    tag: str
    total_seconds: int
    sessions_count: int


class WorkTimerWeeklySummaryResponse(BaseModel):
    """Недельная сводка по рабочему таймеру."""

    week_start: date
    week_end: date
    total_seconds: int
    days: list[WorkTimerDaySummary]
    tasks: list[WorkTimerTaskSummary]
    tags: list[WorkTimerTagSummary]
    sessions: list[WorkTimerSessionResponse]
