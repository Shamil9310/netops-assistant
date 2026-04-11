from __future__ import annotations

from pydantic import BaseModel

from app.schemas.journal import ActivityEntryResponse


class SearchResponse(BaseModel):
    """Ответ поиска с пагинацией."""

    total: int
    limit: int
    offset: int
    results: list[ActivityEntryResponse]


class ArchiveResponse(BaseModel):
    """Ответ архивного запроса с пагинацией."""

    total: int
    limit: int
    offset: int
    results: list[ActivityEntryResponse]
