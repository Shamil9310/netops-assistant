from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.study import (
    StudyBulkCheckpointsRequest,
    StudyCheckpointCreateRequest,
    StudyCheckpointResponse,
    StudyCheckpointUpdateRequest,
    StudyChecklistItemCreateRequest,
    StudyChecklistItemResponse,
    StudyChecklistItemUpdateRequest,
    StudyModuleCreateRequest,
    StudyModuleResponse,
    StudyModuleUpdateRequest,
    StudyPlanCreateRequest,
    StudyPlanResponse,
    StudyPlanUpdateRequest,
    StudyTimerActionRequest,
    StudyWeeklySummaryResponse,
)
from app.services import study as study_service

router = APIRouter()


def _default_week_start() -> date:
    today = datetime.now(UTC).date()
    return today - timedelta(days=today.weekday())


async def _plan_response(
    plan,
    now: datetime | None = None,
) -> StudyPlanResponse:
    return await study_service.build_plan_response(plan, now)


def _checkpoint_response(checkpoint) -> StudyCheckpointResponse:
    return StudyCheckpointResponse(
        id=str(checkpoint.id),
        plan_id=str(checkpoint.plan_id),
        module_id=str(checkpoint.module_id) if checkpoint.module_id else None,
        title=checkpoint.title,
        description=checkpoint.description,
        order_index=checkpoint.order_index,
        progress_percent=checkpoint.progress_percent,
        is_done=checkpoint.is_done,
        completed_at=checkpoint.completed_at,
        created_at=checkpoint.created_at,
        updated_at=checkpoint.updated_at,
    )


def _checklist_item_response(item) -> StudyChecklistItemResponse:
    return StudyChecklistItemResponse(
        id=str(item.id),
        plan_id=str(item.plan_id),
        checkpoint_id=str(item.checkpoint_id) if item.checkpoint_id else None,
        title=item.title,
        description=item.description,
        order_index=item.order_index,
        is_done=item.is_done,
        completed_at=item.completed_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("/plans", response_model=list[StudyPlanResponse])
async def list_plans(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[StudyPlanResponse]:
    plans = await study_service.list_plans(db, current_user.id)
    return [await _plan_response(plan) for plan in plans]


@router.post(
    "/plans", response_model=StudyPlanResponse, status_code=status.HTTP_201_CREATED
)
async def create_plan(
    payload: StudyPlanCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyPlanResponse:
    plan = await study_service.create_plan(db, current_user, payload)
    return await _plan_response(plan)


@router.get("/plans/{plan_id}", response_model=StudyPlanResponse)
async def get_plan(
    plan_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyPlanResponse:
    plan = await study_service.get_plan_by_id(db, current_user.id, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="План не найден"
        )
    return await _plan_response(plan)


@router.patch("/plans/{plan_id}", response_model=StudyPlanResponse)
async def update_plan(
    plan_id: UUID,
    payload: StudyPlanUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyPlanResponse:
    plan = await study_service.get_plan_by_id(db, current_user.id, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="План не найден"
        )
    try:
        updated = await study_service.update_plan(db, plan, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error
    return await _plan_response(updated)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    plan = await study_service.get_plan_by_id(db, current_user.id, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="План не найден"
        )
    await study_service.delete_plan(db, plan)


@router.post(
    "/plans/{plan_id}/modules",
    response_model=StudyModuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_module(
    plan_id: UUID,
    payload: StudyModuleCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyModuleResponse:
    plan = await study_service.get_plan_by_id(db, current_user.id, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="План не найден"
        )
    module = await study_service.create_module(db, plan, payload)
    return StudyModuleResponse(
        id=str(module.id),
        plan_id=str(module.plan_id),
        title=module.title,
        description=module.description,
        order_index=module.order_index,
        created_at=module.created_at,
        updated_at=module.updated_at,
    )


@router.patch("/modules/{module_id}", response_model=StudyModuleResponse)
async def update_module(
    module_id: UUID,
    payload: StudyModuleUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyModuleResponse:
    module = await study_service.get_module_by_id(db, current_user.id, module_id)
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Модуль не найден"
        )
    updated = await study_service.update_module(db, module, payload)
    return StudyModuleResponse(
        id=str(updated.id),
        plan_id=str(updated.plan_id),
        title=updated.title,
        description=updated.description,
        order_index=updated.order_index,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    module = await study_service.get_module_by_id(db, current_user.id, module_id)
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Модуль не найден"
        )
    await study_service.delete_module(db, module)


@router.post(
    "/plans/{plan_id}/checkpoints/bulk",
    response_model=StudyPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bulk_add_checkpoints(
    plan_id: UUID,
    payload: StudyBulkCheckpointsRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyPlanResponse:
    plan = await study_service.get_plan_by_id(db, current_user.id, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="План не найден"
        )
    updated = await study_service.bulk_add_checkpoints(db, plan, payload)
    return await _plan_response(updated)


@router.post(
    "/plans/{plan_id}/checkpoints",
    response_model=StudyCheckpointResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_checkpoint(
    plan_id: UUID,
    payload: StudyCheckpointCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyCheckpointResponse:
    plan = await study_service.get_plan_by_id(db, current_user.id, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="План не найден"
        )
    checkpoint = await study_service.create_checkpoint(db, plan, payload)
    return _checkpoint_response(checkpoint)


@router.patch("/checkpoints/{checkpoint_id}", response_model=StudyCheckpointResponse)
async def update_checkpoint(
    checkpoint_id: UUID,
    payload: StudyCheckpointUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyCheckpointResponse:
    checkpoint = await study_service.get_checkpoint_by_id(
        db, current_user.id, checkpoint_id
    )
    if checkpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Чекпоинт не найден"
        )
    try:
        updated = await study_service.update_checkpoint(db, checkpoint, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    return _checkpoint_response(updated)


@router.delete("/checkpoints/{checkpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkpoint(
    checkpoint_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    checkpoint = await study_service.get_checkpoint_by_id(
        db, current_user.id, checkpoint_id
    )
    if checkpoint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Чекпоинт не найден"
        )
    await study_service.delete_checkpoint(db, checkpoint)


@router.post(
    "/plans/{plan_id}/checklist-items",
    response_model=StudyChecklistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_checklist_item(
    plan_id: UUID,
    payload: StudyChecklistItemCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyChecklistItemResponse:
    plan = await study_service.get_plan_by_id(db, current_user.id, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="План не найден"
        )
    try:
        item = await study_service.create_checklist_item(db, plan, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    return _checklist_item_response(item)


@router.patch("/checklist-items/{item_id}", response_model=StudyChecklistItemResponse)
async def update_checklist_item(
    item_id: UUID,
    payload: StudyChecklistItemUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyChecklistItemResponse:
    item = await study_service.get_checklist_item_by_id(db, current_user.id, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пункт чеклиста не найден"
        )
    try:
        updated = await study_service.update_checklist_item(db, item, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
    return _checklist_item_response(updated)


@router.delete("/checklist-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist_item(
    item_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    item = await study_service.get_checklist_item_by_id(db, current_user.id, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пункт чеклиста не найден"
        )
    await study_service.delete_checklist_item(db, item)


@router.post("/plans/{plan_id}/timer", response_model=StudyPlanResponse)
async def change_timer(
    plan_id: UUID,
    payload: StudyTimerActionRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> StudyPlanResponse:
    plan = await study_service.get_plan_by_id(db, current_user.id, plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="План не найден"
        )
    try:
        updated = await study_service.change_timer(db, plan, current_user, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        ) from error
    return await _plan_response(updated)


@router.get("/weekly-summary", response_model=StudyWeeklySummaryResponse)
async def weekly_summary(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    week_start: date | None = Query(default=None),
) -> StudyWeeklySummaryResponse:
    resolved_week_start = week_start or _default_week_start()
    return await study_service.build_weekly_summary(
        db, current_user, resolved_week_start
    )
