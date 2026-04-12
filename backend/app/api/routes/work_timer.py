from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.schemas.work_timer import (
    WorkTimerTaskCreateRequest,
    WorkTimerTaskResponse,
    WorkTimerTaskUpdateRequest,
    WorkTimerTimerActionRequest,
    WorkTimerWeeklySummaryResponse,
)
from app.services import work_timer as work_timer_service

router = APIRouter()


@router.get("/tasks", response_model=list[WorkTimerTaskResponse])
async def list_tasks(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[WorkTimerTaskResponse]:
    return await work_timer_service.list_tasks_as_response(db, current_user.id)


@router.post(
    "/tasks", response_model=WorkTimerTaskResponse, status_code=status.HTTP_201_CREATED
)
async def create_task(
    payload: WorkTimerTaskCreateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WorkTimerTaskResponse:
    return await work_timer_service.create_task(db, current_user, payload)


@router.patch("/tasks/{task_id}", response_model=WorkTimerTaskResponse)
async def update_task(
    task_id: UUID,
    payload: WorkTimerTaskUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WorkTimerTaskResponse:
    task = await work_timer_service.get_task(db, current_user.id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )
    try:
        return await work_timer_service.update_task(db, task, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    task = await work_timer_service.get_task(db, current_user.id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )
    await work_timer_service.delete_task(db, task)


@router.post("/tasks/{task_id}/timer", response_model=WorkTimerTaskResponse)
async def change_timer(
    task_id: UUID,
    payload: WorkTimerTimerActionRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WorkTimerTaskResponse:
    task = await work_timer_service.get_task(db, current_user.id, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )
    try:
        return await work_timer_service.change_timer(db, task, current_user, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@router.get("/weekly-summary", response_model=WorkTimerWeeklySummaryResponse)
async def weekly_summary(
    current_user: CurrentUser,
    week_start: date = Query(...),
    db: AsyncSession = Depends(get_db),
) -> WorkTimerWeeklySummaryResponse:
    try:
        return await work_timer_service.get_weekly_summary(
            db, current_user.id, week_start
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
