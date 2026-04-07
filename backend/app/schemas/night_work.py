from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.night_work import (
    NightWorkBlockStatus,
    NightWorkPlanStatus,
    NightWorkStepStatus,
)


class NightWorkStepResponse(BaseModel):
    id: str
    block_id: str
    title: str
    description: str | None
    status: str
    order_index: int
    is_rollback: bool
    is_post_action: bool
    actual_result: str | None
    executor_comment: str | None
    collaborators: list[str]
    handoff_to: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class NightWorkBlockResponse(BaseModel):
    id: str
    plan_id: str
    sr_number: str | None
    title: str
    description: str | None
    status: str
    order_index: int
    started_at: datetime | None
    finished_at: datetime | None
    result_comment: str | None
    created_at: datetime
    steps: list[NightWorkStepResponse]


class NightWorkPlanResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str | None
    status: str
    scheduled_at: datetime | None
    participants: list[str]
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
    blocks: list[NightWorkBlockResponse]


# ---------------------------------------------------------------------------
# Запросы на создание/обновление
# ---------------------------------------------------------------------------


class NightWorkPlanCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=256)
    description: str | None = None
    scheduled_at: datetime | None = None
    participants: list[str] = Field(default_factory=list)


class NightWorkPlanUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=256)
    description: str | None = None
    scheduled_at: datetime | None = None
    participants: list[str] | None = None


class NightWorkPlanStatusRequest(BaseModel):
    """Запрос на изменение статуса плана."""

    status: NightWorkPlanStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None


class NightWorkBlockCreateRequest(BaseModel):
    sr_number: str | None = Field(default=None, max_length=128)
    title: str = Field(min_length=2, max_length=256)
    description: str | None = None
    order_index: int = Field(default=0, ge=0)


class NightWorkBlockStatusRequest(BaseModel):
    """Запрос на изменение статуса блока."""

    status: NightWorkBlockStatus
    result_comment: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class NightWorkStepCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=256)
    description: str | None = None
    order_index: int = Field(default=0, ge=0)
    is_rollback: bool = False
    is_post_action: bool = False


class NightWorkStepStatusRequest(BaseModel):
    """Запрос на изменение статуса шага с фиксацией результата."""

    status: NightWorkStepStatus
    actual_result: str | None = None
    executor_comment: str | None = None
    collaborators: list[str] | None = None
    handoff_to: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class CreatePlanFromTemplateRequest(BaseModel):
    template_id: str
    title: str | None = Field(default=None, min_length=2, max_length=256)
    variables: dict[str, str] = Field(default_factory=dict)
    scheduled_at: datetime | None = None
