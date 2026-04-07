from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.template import PlanTemplate
from app.schemas.template import (
    PlanTemplateCreateRequest,
    PlanTemplateResponse,
    PlanTemplateUpdateRequest,
)
from app.services import template as template_service

router = APIRouter()


def _to_response(template: PlanTemplate) -> PlanTemplateResponse:
    return PlanTemplateResponse(
        id=str(template.id),
        user_id=str(template.user_id),
        key=template.key,
        name=template.name,
        category=template.category,
        description=template.description,
        template_payload=template.template_payload,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("", response_model=list[PlanTemplateResponse])
async def list_templates(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    category: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> list[PlanTemplateResponse]:
    templates = await template_service.list_templates(db, current_user.id, category, is_active)
    return [_to_response(template) for template in templates]


@router.get("/defaults")
async def default_templates_catalog() -> list[dict[str, object]]:
    """Возвращает встроенный каталог типовых шаблонов (read-only)."""
    return template_service.get_default_template_catalog()


@router.post("/import-defaults", response_model=list[PlanTemplateResponse], status_code=status.HTTP_201_CREATED)
async def import_defaults(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[PlanTemplateResponse]:
    """Импортирует дефолтные шаблоны в библиотеку текущего пользователя."""
    imported = await template_service.import_default_templates(db, current_user.id)
    return [_to_response(template) for template in imported]


@router.post("", response_model=PlanTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: PlanTemplateCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> PlanTemplateResponse:
    normalized_key = template_service.normalize_template_key(payload.key)
    existing = await template_service.get_template_by_key(db, normalized_key, current_user.id)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Шаблон с таким ключом уже существует")

    try:
        template = await template_service.create_template(
            db,
            user_id=current_user.id,
            key=payload.key,
            name=payload.name,
            category=payload.category,
            description=payload.description,
            template_payload=payload.template_payload,
            is_active=payload.is_active,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return _to_response(template)


@router.get("/{template_id}", response_model=PlanTemplateResponse)
async def get_template(
    template_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> PlanTemplateResponse:
    template = await template_service.get_template_by_id(db, template_id, current_user.id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон не найден")
    return _to_response(template)


@router.patch("/{template_id}", response_model=PlanTemplateResponse)
async def update_template(
    template_id: UUID,
    payload: PlanTemplateUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> PlanTemplateResponse:
    template = await template_service.get_template_by_id(db, template_id, current_user.id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон не найден")

    if payload.key is not None:
        normalized_key = template_service.normalize_template_key(payload.key)
        existing = await template_service.get_template_by_key(db, normalized_key, current_user.id)
        if existing is not None and existing.id != template.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Шаблон с таким ключом уже существует")

    try:
        updated = await template_service.update_template(
            db,
            template=template,
            key=payload.key,
            name=payload.name,
            category=payload.category,
            description=payload.description,
            template_payload=payload.template_payload,
            is_active=payload.is_active,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return _to_response(updated)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    template = await template_service.get_template_by_id(db, template_id, current_user.id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон не найден")
    await template_service.delete_template(db, template)
