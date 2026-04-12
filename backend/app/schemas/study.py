from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.study import (
    StudyPlanStatus,
    StudyPlanTrack,
    StudySessionStatus,
)


class StudyModuleResponse(BaseModel):
    """Представление блока (модуля) учебного плана."""

    id: str
    plan_id: str
    title: str
    description: str | None
    order_index: int
    created_at: datetime
    updated_at: datetime


class StudyCheckpointResponse(BaseModel):
    """Представление этапа учебного плана."""

    id: str
    plan_id: str
    module_id: str | None
    title: str
    description: str | None
    order_index: int
    progress_percent: int
    is_done: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class StudyChecklistItemResponse(BaseModel):
    """Представление пункта чеклиста."""

    id: str
    plan_id: str
    checkpoint_id: str | None
    title: str
    description: str | None
    order_index: int
    is_done: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class StudySessionResponse(BaseModel):
    """Представление таймерной сессии учёбы."""

    id: str
    plan_id: str
    checkpoint_id: str | None
    status: StudySessionStatus
    progress_percent: int
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int
    created_at: datetime
    updated_at: datetime


class StudyPlanResponse(BaseModel):
    """Полное представление учебного плана."""

    id: str
    user_id: str
    title: str
    description: str | None
    track: StudyPlanTrack
    status: StudyPlanStatus
    total_seconds: int
    active_session_id: str | None
    active_session_started_at: datetime | None
    created_at: datetime
    updated_at: datetime
    modules: list[StudyModuleResponse]
    checkpoints: list[StudyCheckpointResponse]
    checklist_items: list[StudyChecklistItemResponse]
    sessions: list[StudySessionResponse]


class StudyPlanCreateRequest(BaseModel):
    """Запрос на создание учебного плана."""

    title: str = Field(min_length=2, max_length=256)
    description: str | None = None
    track: StudyPlanTrack = StudyPlanTrack.PYTHON
    status: StudyPlanStatus = StudyPlanStatus.DRAFT


class StudyPlanUpdateRequest(BaseModel):
    """Запрос на обновление учебного плана."""

    title: str | None = Field(default=None, min_length=2, max_length=256)
    description: str | None = None
    track: StudyPlanTrack | None = None
    status: StudyPlanStatus | None = None


class StudyModuleCreateRequest(BaseModel):
    """Запрос на создание модуля."""

    title: str = Field(min_length=2, max_length=256)
    description: str | None = None
    order_index: int = Field(default=0, ge=0)


class StudyModuleUpdateRequest(BaseModel):
    """Запрос на обновление модуля."""

    title: str | None = Field(default=None, min_length=2, max_length=256)
    description: str | None = None
    order_index: int | None = Field(default=None, ge=0)


class StudyCheckpointCreateRequest(BaseModel):
    """Запрос на создание чекпоинта."""

    title: str = Field(min_length=2, max_length=256)
    description: str | None = None
    module_id: UUID | None = None
    order_index: int = Field(default=0, ge=0)


class StudyBulkCheckpointsRequest(BaseModel):
    """Запрос на массовое создание тем из роадмапа.

    Роадмап передаётся как список секций, каждая из которых содержит
    название модуля и список тем. Если module_title пустой — темы создаются
    без привязки к модулю (или к существующему последнему модулю).
    """

    class Section(BaseModel):
        """Секция роадмапа: опциональный заголовок модуля и список тем."""

        module_title: str | None = None
        topics: list[str]

    sections: list[Section]


class StudyCheckpointUpdateRequest(BaseModel):
    """Запрос на обновление чекпоинта."""

    title: str | None = Field(default=None, min_length=2, max_length=256)
    description: str | None = None
    order_index: int | None = Field(default=None, ge=0)
    is_done: bool | None = None


class StudyChecklistItemCreateRequest(BaseModel):
    """Запрос на создание пункта чеклиста."""

    title: str = Field(min_length=2, max_length=256)
    description: str | None = None
    checkpoint_id: UUID | None = None
    order_index: int = Field(default=0, ge=0)


class StudyChecklistItemUpdateRequest(BaseModel):
    """Запрос на обновление пункта чеклиста."""

    title: str | None = Field(default=None, min_length=2, max_length=256)
    description: str | None = None
    checkpoint_id: UUID | None = None
    order_index: int | None = Field(default=None, ge=0)
    is_done: bool | None = None


class StudyTimerActionRequest(BaseModel):
    """Запрос на действие с таймером."""

    action: Literal["start", "pause", "stop"]
    checkpoint_id: UUID | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)


class StudyWeeklyDaySummary(BaseModel):
    """Сводка по одному дню недели."""

    day: date
    total_seconds: int
    sessions_count: int


class StudyWeeklyPlanSummary(BaseModel):
    """Сводка по одному учебному плану за неделю."""

    plan_id: str
    title: str
    total_seconds: int
    sessions_count: int


class StudyCheckpointCompletionSummary(BaseModel):
    """Информация о завершённом чекпоинте."""

    checkpoint_id: str
    plan_id: str
    plan_title: str
    title: str
    completed_at: datetime


class StudyWeeklySummaryResponse(BaseModel):
    """Недельная сводка по учёбе."""

    week_start: date
    week_end: date
    total_seconds: int
    days: list[StudyWeeklyDaySummary]
    plans: list[StudyWeeklyPlanSummary]
    sessions: list[StudySessionResponse]
    completed_checkpoints: list[StudyCheckpointCompletionSummary]
