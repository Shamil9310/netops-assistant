from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PlanTemplateResponse(BaseModel):
    id: str
    user_id: str
    key: str
    name: str
    category: str
    description: str | None
    template_payload: dict[str, object]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PlanTemplateCreateRequest(BaseModel):
    key: str = Field(min_length=3, max_length=64)
    name: str = Field(min_length=2, max_length=128)
    category: str = Field(min_length=2, max_length=64)
    description: str | None = None
    template_payload: dict[str, object] = Field(default_factory=dict)
    is_active: bool = True


class PlanTemplateUpdateRequest(BaseModel):
    key: str | None = Field(default=None, min_length=3, max_length=64)
    name: str | None = Field(default=None, min_length=2, max_length=128)
    category: str | None = Field(default=None, min_length=2, max_length=64)
    description: str | None = None
    template_payload: dict[str, object] | None = None
    is_active: bool | None = None
