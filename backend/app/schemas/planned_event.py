from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.planned_event import PlannedEventType


class PlannedEventResponse(BaseModel):
    """Полное представление планового события."""

    id: str
    user_id: str
    event_type: str
    title: str
    description: str | None
    external_ref: str | None
    scheduled_at: datetime
    is_completed: bool
    linked_journal_entry_id: str | None
    created_at: datetime
    updated_at: datetime


class PlannedEventCreateRequest(BaseModel):
    """Запрос на создание планового события."""

    event_type: PlannedEventType
    title: str = Field(min_length=2, max_length=256)
    description: str | None = None
    external_ref: str | None = Field(default=None, max_length=128)
    scheduled_at: datetime


class PlannedEventUpdateRequest(BaseModel):
    """Запрос на обновление планового события. Все поля опциональны."""

    event_type: PlannedEventType | None = None
    title: str | None = Field(default=None, min_length=2, max_length=256)
    description: str | None = None
    external_ref: str | None = Field(default=None, max_length=128)
    scheduled_at: datetime | None = None
    is_completed: bool | None = None
    linked_journal_entry_id: UUID | None = None
