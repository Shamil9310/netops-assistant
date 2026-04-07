from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.night_work import (
    NightWorkBlock,
    NightWorkPlan,
    NightWorkPlanStatus,
    NightWorkStep,
)
from app.schemas.night_work import (
    CreatePlanFromTemplateRequest,
    NightWorkBlockCreateRequest,
    NightWorkBlockResponse,
    NightWorkBlockStatusRequest,
    NightWorkPlanCreateRequest,
    NightWorkPlanResponse,
    NightWorkPlanStatusRequest,
    NightWorkPlanUpdateRequest,
    NightWorkStepCreateRequest,
    NightWorkStepResponse,
    NightWorkStepStatusRequest,
)
from app.services import template as template_service
from app.services import night_work as nw_service

router = APIRouter()


def _step_to_response(step: NightWorkStep) -> NightWorkStepResponse:
    return NightWorkStepResponse(
        id=str(step.id),
        block_id=str(step.block_id),
        title=step.title,
        description=step.description,
        status=step.status,
        order_index=step.order_index,
        is_rollback=step.is_rollback,
        is_post_action=step.is_post_action,
        actual_result=step.actual_result,
        executor_comment=step.executor_comment,
        collaborators=step.collaborators,
        handoff_to=step.handoff_to,
        started_at=step.started_at,
        finished_at=step.finished_at,
        created_at=step.created_at,
    )


def _block_to_response(block: NightWorkBlock) -> NightWorkBlockResponse:
    return NightWorkBlockResponse(
        id=str(block.id),
        plan_id=str(block.plan_id),
        sr_number=block.sr_number,
        title=block.title,
        description=block.description,
        status=block.status,
        order_index=block.order_index,
        started_at=block.started_at,
        finished_at=block.finished_at,
        result_comment=block.result_comment,
        created_at=block.created_at,
        steps=[_step_to_response(s) for s in block.steps],
    )


def _plan_to_response(plan: NightWorkPlan) -> NightWorkPlanResponse:
    return NightWorkPlanResponse(
        id=str(plan.id),
        user_id=str(plan.user_id),
        title=plan.title,
        description=plan.description,
        status=plan.status,
        scheduled_at=plan.scheduled_at,
        participants=plan.participants,
        started_at=plan.started_at,
        finished_at=plan.finished_at,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        blocks=[_block_to_response(b) for b in plan.blocks],
    )


# ---------------------------------------------------------------------------
# Планы
# ---------------------------------------------------------------------------


@router.get("", response_model=list[NightWorkPlanResponse])
async def list_plans(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status: NightWorkPlanStatus | None = Query(default=None),
) -> list[NightWorkPlanResponse]:
    """Список планов ночных работ текущего пользователя."""
    plans = await nw_service.list_plans(db, current_user.id, status)
    return [_plan_to_response(p) for p in plans]


@router.post("", response_model=NightWorkPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: NightWorkPlanCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> NightWorkPlanResponse:
    """Создаёт новый план ночных работ в статусе DRAFT."""
    plan = await nw_service.create_plan(
        db,
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        scheduled_at=payload.scheduled_at,
        participants=payload.participants,
    )
    return _plan_to_response(plan)


@router.post("/from-template", response_model=NightWorkPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan_from_template(
    payload: CreatePlanFromTemplateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> NightWorkPlanResponse:
    """Создаёт новый план на основе сохранённого шаблона пользователя."""
    try:
        template_id = UUID(payload.template_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Некорректный template_id") from error

    template = await template_service.get_template_by_id(db, template_id, current_user.id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон не найден")

    try:
        plan = await nw_service.create_plan_from_template(
            db,
            user_id=current_user.id,
            template=template,
            variables=payload.variables,
            title=payload.title,
            scheduled_at=payload.scheduled_at,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    return _plan_to_response(plan)


@router.get("/{plan_id}", response_model=NightWorkPlanResponse)
async def get_plan(
    plan_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> NightWorkPlanResponse:
    """Возвращает план с блоками и шагами. Только владелец."""
    plan = await nw_service.get_plan_by_id(db, plan_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План не найден")
    return _plan_to_response(plan)


@router.patch("/{plan_id}", response_model=NightWorkPlanResponse)
async def update_plan(
    plan_id: UUID,
    payload: NightWorkPlanUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> NightWorkPlanResponse:
    """Обновляет поля плана. Разрешено только в статусе DRAFT."""
    plan = await nw_service.get_plan_by_id(db, plan_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План не найден")
    if plan.status != NightWorkPlanStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Редактирование плана доступно только в статусе DRAFT",
        )
    updated = await nw_service.update_plan(
        db,
        plan,
        payload.title,
        payload.description,
        payload.scheduled_at,
        payload.participants,
    )
    return _plan_to_response(updated)


@router.patch("/{plan_id}/status", response_model=NightWorkPlanResponse)
async def change_plan_status(
    plan_id: UUID,
    payload: NightWorkPlanStatusRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> NightWorkPlanResponse:
    """Переводит план в новый статус."""
    plan = await nw_service.get_plan_by_id(db, plan_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План не найден")
    try:
        updated = await nw_service.update_plan_status(
            db, plan, payload.status, payload.started_at, payload.finished_at
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return _plan_to_response(updated)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удаляет план. Только DRAFT или CANCELLED."""
    plan = await nw_service.get_plan_by_id(db, plan_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План не найден")
    if plan.status not in (NightWorkPlanStatus.DRAFT.value, NightWorkPlanStatus.CANCELLED.value):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Удаление доступно только для планов в статусе DRAFT или CANCELLED",
        )
    await nw_service.delete_plan(db, plan)


# ---------------------------------------------------------------------------
# Блоки (SR)
# ---------------------------------------------------------------------------


@router.post("/{plan_id}/blocks", response_model=NightWorkBlockResponse, status_code=status.HTTP_201_CREATED)
async def add_block(
    plan_id: UUID,
    payload: NightWorkBlockCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> NightWorkBlockResponse:
    """Добавляет блок (SR/изменение) в план."""
    plan = await nw_service.get_plan_by_id(db, plan_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План не найден")
    block = await nw_service.add_block(
        db, plan,
        title=payload.title,
        description=payload.description,
        sr_number=payload.sr_number,
        order_index=payload.order_index,
    )
    return _block_to_response(block)


@router.patch("/{plan_id}/blocks/{block_id}/status", response_model=NightWorkBlockResponse)
async def update_block_status(
    plan_id: UUID,
    block_id: UUID,
    payload: NightWorkBlockStatusRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> NightWorkBlockResponse:
    """Обновляет статус блока и фиксирует результат."""
    plan = await nw_service.get_plan_by_id(db, plan_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План не найден")
    block = await nw_service.get_block_by_id(db, block_id, plan_id)
    if block is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Блок не найден")
    try:
        updated = await nw_service.update_block_status(
            db, block, payload.status, payload.result_comment, payload.started_at, payload.finished_at
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return _block_to_response(updated)


# ---------------------------------------------------------------------------
# Шаги
# ---------------------------------------------------------------------------


@router.post(
    "/{plan_id}/blocks/{block_id}/steps",
    response_model=NightWorkStepResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_step(
    plan_id: UUID,
    block_id: UUID,
    payload: NightWorkStepCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> NightWorkStepResponse:
    """Добавляет шаг в блок плана."""
    plan = await nw_service.get_plan_by_id(db, plan_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План не найден")
    block = await nw_service.get_block_by_id(db, block_id, plan_id)
    if block is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Блок не найден")
    step = await nw_service.add_step(
        db, block,
        title=payload.title,
        description=payload.description,
        order_index=payload.order_index,
        is_rollback=payload.is_rollback,
        is_post_action=payload.is_post_action,
    )
    return _step_to_response(step)


@router.patch(
    "/{plan_id}/blocks/{block_id}/steps/{step_id}/status",
    response_model=NightWorkStepResponse,
)
async def update_step_status(
    plan_id: UUID,
    block_id: UUID,
    step_id: UUID,
    payload: NightWorkStepStatusRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> NightWorkStepResponse:
    """Обновляет статус шага и фиксирует фактический результат исполнения."""
    plan = await nw_service.get_plan_by_id(db, plan_id, current_user.id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="План не найден")
    block = await nw_service.get_block_by_id(db, block_id, plan_id)
    if block is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Блок не найден")
    step = await nw_service.get_step_by_id(db, step_id, block_id)
    if step is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаг не найден")
    try:
        updated = await nw_service.update_step_status(
            db, step, payload.status,
            payload.actual_result, payload.executor_comment,
            payload.collaborators,
            payload.handoff_to,
            payload.started_at, payload.finished_at,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return _step_to_response(updated)
