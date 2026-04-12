from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import TypedDict
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.study import (
    StudyCheckpoint,
    StudyChecklistItem,
    StudyModule,
    StudyPlan,
    StudyPlanStatus,
    StudyPlanTrack,
    StudySession,
    StudySessionStatus,
)
from app.models.user import User
from app.schemas.study import (
    StudyBulkCheckpointsRequest,
    StudyCheckpointCompletionSummary,
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
    StudySessionResponse,
    StudyTimerActionRequest,
    StudyWeeklyDaySummary,
    StudyWeeklyPlanSummary,
    StudyWeeklySummaryResponse,
)

_PLAN_ALLOWED_TRANSITIONS: dict[StudyPlanStatus, set[StudyPlanStatus]] = {
    StudyPlanStatus.DRAFT: {StudyPlanStatus.ACTIVE, StudyPlanStatus.CANCELLED},
    StudyPlanStatus.ACTIVE: {StudyPlanStatus.COMPLETED, StudyPlanStatus.CANCELLED},
    StudyPlanStatus.COMPLETED: set(),
    StudyPlanStatus.CANCELLED: set(),
}


class _WeeklyPlanAggregate(TypedDict):
    plan_id: str
    title: str
    total_seconds: int
    sessions_count: int


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_progress_percent(value: int | None) -> int:
    if value is None:
        return 0
    if value < 0:
        return 0
    if value > 100:
        return 100
    return value


def _mark_checkpoint_progress(
    checkpoint: StudyCheckpoint, progress_percent: int, now: datetime | None = None
) -> None:
    # Прогресс — итоговый процент освоения темы, а не прирост за сессию.
    # Берём максимум: прогресс не может уменьшиться при повторном сохранении.
    normalized_progress = _normalize_progress_percent(progress_percent)
    checkpoint.progress_percent = max(checkpoint.progress_percent, normalized_progress)
    if checkpoint.progress_percent >= 100:
        checkpoint.is_done = True
        checkpoint.completed_at = now or _utc_now()


def _checkpoint_response(checkpoint: StudyCheckpoint) -> StudyCheckpointResponse:
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


def _session_response(
    study_session: StudySession, now: datetime | None = None
) -> StudySessionResponse:
    return StudySessionResponse(
        id=str(study_session.id),
        plan_id=str(study_session.plan_id),
        checkpoint_id=(
            str(study_session.checkpoint_id) if study_session.checkpoint_id else None
        ),
        status=StudySessionStatus(study_session.status),
        progress_percent=study_session.progress_percent,
        started_at=study_session.started_at,
        ended_at=study_session.ended_at,
        duration_seconds=_session_duration_seconds(study_session, now),
        created_at=study_session.created_at,
        updated_at=study_session.updated_at,
    )


def _validate_plan_transition(
    current_status: StudyPlanStatus,
    next_status: StudyPlanStatus,
) -> None:
    if current_status == next_status:
        return
    if next_status not in _PLAN_ALLOWED_TRANSITIONS[current_status]:
        raise ValueError(
            f"Недопустимый переход статуса плана: {current_status.value} -> {next_status.value}"
        )


def _session_duration_seconds(
    session: StudySession, now: datetime | None = None
) -> int:
    finish = session.ended_at or now or _utc_now()
    delta = finish - session.started_at
    if delta.total_seconds() <= 0:
        return 0
    return int(delta.total_seconds())


def _plan_total_seconds(plan: StudyPlan, now: datetime | None = None) -> int:
    return sum(_session_duration_seconds(session, now) for session in plan.sessions)


def _load_plan_query(user_id: UUID) -> Select[tuple[StudyPlan]]:
    return (
        select(StudyPlan)
        .where(StudyPlan.user_id == user_id)
        .options(
            selectinload(StudyPlan.checkpoints),
            selectinload(StudyPlan.checklist_items),
            selectinload(StudyPlan.sessions),
        )
        .order_by(StudyPlan.created_at.desc())
    )


async def list_plans(session: AsyncSession, user_id: UUID) -> list[StudyPlan]:
    result = await session.execute(_load_plan_query(user_id))
    return list(result.scalars().all())


async def get_checkpoint_by_id(
    session: AsyncSession,
    user_id: UUID,
    checkpoint_id: UUID,
) -> StudyCheckpoint | None:
    result = await session.execute(
        select(StudyCheckpoint)
        .join(StudyPlan, StudyPlan.id == StudyCheckpoint.plan_id)
        .where(StudyCheckpoint.id == checkpoint_id)
        .where(StudyPlan.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_checklist_item_by_id(
    session: AsyncSession,
    user_id: UUID,
    item_id: UUID,
) -> StudyChecklistItem | None:
    result = await session.execute(
        select(StudyChecklistItem)
        .join(StudyPlan, StudyPlan.id == StudyChecklistItem.plan_id)
        .where(StudyChecklistItem.id == item_id)
        .where(StudyPlan.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_plan_by_id(
    session: AsyncSession,
    user_id: UUID,
    plan_id: UUID,
) -> StudyPlan | None:
    result = await session.execute(
        _load_plan_query(user_id).where(StudyPlan.id == plan_id)
    )
    return result.scalar_one_or_none()


async def get_module_by_id(
    session: AsyncSession,
    user_id: UUID,
    module_id: UUID,
) -> StudyModule | None:
    result = await session.execute(
        select(StudyModule)
        .join(StudyPlan, StudyPlan.id == StudyModule.plan_id)
        .where(StudyModule.id == module_id)
        .where(StudyPlan.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_module(
    session: AsyncSession,
    plan: StudyPlan,
    payload: StudyModuleCreateRequest,
) -> StudyModule:
    module = StudyModule(
        plan_id=plan.id,
        title=payload.title.strip(),
        description=_normalize_text(payload.description),
        order_index=payload.order_index,
    )
    session.add(module)
    await session.commit()
    await session.refresh(module)
    return module


async def update_module(
    session: AsyncSession,
    module: StudyModule,
    payload: StudyModuleUpdateRequest,
) -> StudyModule:
    if payload.title is not None:
        module.title = payload.title.strip()
    if "description" in payload.model_fields_set:
        module.description = _normalize_text(payload.description)
    if payload.order_index is not None:
        module.order_index = payload.order_index
    await session.commit()
    await session.refresh(module)
    return module


async def delete_module(session: AsyncSession, module: StudyModule) -> None:
    await session.delete(module)
    await session.commit()


async def bulk_add_checkpoints(
    session: AsyncSession,
    plan: StudyPlan,
    payload: StudyBulkCheckpointsRequest,
) -> StudyPlan:
    """Создаёт модули и темы из роадмапа за одну транзакцию.

    Каждая секция с module_title становится новым модулем.
    Темы без секции (или с пустым module_title) добавляются без модуля.
    Порядок тем внутри плана продолжается с текущего максимума.
    """
    current_checkpoint_order = len(plan.checkpoints)

    for section in payload.sections:
        module_id: UUID | None = None

        if section.module_title:
            # Определяем порядковый номер нового модуля по текущему количеству.
            next_module_order = len(plan.modules)
            module = StudyModule(
                plan_id=plan.id,
                title=section.module_title.strip(),
                order_index=next_module_order,
            )
            session.add(module)
            # Флушим, чтобы получить id модуля до создания тем.
            await session.flush()
            module_id = module.id

        for topic_title in section.topics:
            stripped = topic_title.strip()
            if not stripped:
                continue
            session.add(
                StudyCheckpoint(
                    plan_id=plan.id,
                    module_id=module_id,
                    title=stripped,
                    order_index=current_checkpoint_order,
                    progress_percent=0,
                )
            )
            current_checkpoint_order += 1

    await session.commit()
    return await _refresh_plan(session, plan.id)


async def create_plan(
    session: AsyncSession,
    user: User,
    payload: StudyPlanCreateRequest,
) -> StudyPlan:
    plan = StudyPlan(
        user_id=user.id,
        title=payload.title.strip(),
        description=_normalize_text(payload.description),
        track=payload.track.value,
        status=payload.status.value,
    )
    session.add(plan)
    await session.commit()
    return await _refresh_plan(session, plan.id)


async def update_plan(
    session: AsyncSession,
    plan: StudyPlan,
    payload: StudyPlanUpdateRequest,
) -> StudyPlan:
    if payload.title is not None:
        plan.title = payload.title.strip()
    if "description" in payload.model_fields_set:
        plan.description = _normalize_text(payload.description)
    if payload.track is not None:
        plan.track = payload.track.value
    if payload.status is not None:
        next_status = payload.status
        _validate_plan_transition(StudyPlanStatus(plan.status), next_status)
        plan.status = next_status.value
    await session.commit()
    await session.refresh(plan)
    return plan


async def delete_plan(session: AsyncSession, plan: StudyPlan) -> None:
    await session.delete(plan)
    await session.commit()


async def create_checkpoint(
    session: AsyncSession,
    plan: StudyPlan,
    payload: StudyCheckpointCreateRequest,
) -> StudyCheckpoint:
    checkpoint = StudyCheckpoint(
        plan_id=plan.id,
        title=payload.title.strip(),
        description=_normalize_text(payload.description),
        order_index=payload.order_index,
        progress_percent=0,
    )
    session.add(checkpoint)
    await session.commit()
    await session.refresh(checkpoint)
    return checkpoint


async def update_checkpoint(
    session: AsyncSession,
    checkpoint: StudyCheckpoint,
    payload: StudyCheckpointUpdateRequest,
) -> StudyCheckpoint:
    if payload.title is not None:
        checkpoint.title = payload.title.strip()
    if "description" in payload.model_fields_set:
        checkpoint.description = _normalize_text(payload.description)
    if payload.order_index is not None:
        checkpoint.order_index = payload.order_index
    if payload.is_done is not None:
        checkpoint.is_done = payload.is_done
        checkpoint.progress_percent = (
            100 if payload.is_done else checkpoint.progress_percent
        )
        checkpoint.completed_at = _utc_now() if payload.is_done else None
    await session.commit()
    await session.refresh(checkpoint)
    return checkpoint


async def delete_checkpoint(session: AsyncSession, checkpoint: StudyCheckpoint) -> None:
    await session.delete(checkpoint)
    await session.commit()


async def create_checklist_item(
    session: AsyncSession,
    plan: StudyPlan,
    payload: StudyChecklistItemCreateRequest,
) -> StudyChecklistItem:
    if payload.checkpoint_id is not None:
        checkpoint = await session.get(StudyCheckpoint, payload.checkpoint_id)
        if checkpoint is None or checkpoint.plan_id != plan.id:
            raise ValueError("Чекпоинт не найден в выбранном учебном плане")

    item = StudyChecklistItem(
        plan_id=plan.id,
        checkpoint_id=payload.checkpoint_id,
        title=payload.title.strip(),
        description=_normalize_text(payload.description),
        order_index=payload.order_index,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def update_checklist_item(
    session: AsyncSession,
    item: StudyChecklistItem,
    payload: StudyChecklistItemUpdateRequest,
) -> StudyChecklistItem:
    if payload.title is not None:
        item.title = payload.title.strip()
    if "description" in payload.model_fields_set:
        item.description = _normalize_text(payload.description)
    if "checkpoint_id" in payload.model_fields_set:
        if payload.checkpoint_id is None:
            item.checkpoint_id = None
        else:
            checkpoint = await session.get(StudyCheckpoint, payload.checkpoint_id)
            if checkpoint is None or checkpoint.plan_id != item.plan_id:
                raise ValueError("Чекпоинт не найден в выбранном учебном плане")
            item.checkpoint_id = payload.checkpoint_id
    if payload.order_index is not None:
        item.order_index = payload.order_index
    if payload.is_done is not None:
        item.is_done = payload.is_done
        item.completed_at = _utc_now() if payload.is_done else None
    await session.commit()
    await session.refresh(item)
    return item


async def delete_checklist_item(
    session: AsyncSession, item: StudyChecklistItem
) -> None:
    await session.delete(item)
    await session.commit()


async def get_active_session_for_user(
    session: AsyncSession,
    user_id: UUID,
) -> StudySession | None:
    result = await session.execute(
        select(StudySession)
        .join(StudyPlan, StudyPlan.id == StudySession.plan_id)
        .where(StudyPlan.user_id == user_id)
        .where(StudySession.ended_at.is_(None))
        .order_by(StudySession.started_at.desc())
    )
    return result.scalar_one_or_none()


async def get_active_session_for_plan(
    session: AsyncSession,
    plan_id: UUID,
) -> StudySession | None:
    result = await session.execute(
        select(StudySession)
        .where(StudySession.plan_id == plan_id)
        .where(StudySession.ended_at.is_(None))
        .order_by(StudySession.started_at.desc())
    )
    return result.scalar_one_or_none()


async def change_timer(
    session: AsyncSession,
    plan: StudyPlan,
    user: User,
    action: StudyTimerActionRequest,
    now: datetime | None = None,
) -> StudyPlan:
    current_now = now or _utc_now()
    current_status = StudyPlanStatus(plan.status)

    if action.action == "start":
        if current_status in {StudyPlanStatus.COMPLETED, StudyPlanStatus.CANCELLED}:
            raise ValueError(
                "Нельзя запускать таймер у завершённого или отменённого плана"
            )
        if action.checkpoint_id is None:
            raise ValueError("Для старта таймера нужно выбрать тему")
        checkpoint = await get_checkpoint_by_id(session, user.id, action.checkpoint_id)
        if checkpoint is None or checkpoint.plan_id != plan.id:
            raise ValueError("Тема не найдена в выбранном учебном плане")
        if checkpoint.is_done:
            raise ValueError("Эта тема уже закрыта")

        active_session = await get_active_session_for_user(session, user.id)
        if active_session is not None and active_session.plan_id != plan.id:
            raise ValueError(
                "Сначала останови активный таймер у другого учебного плана"
            )
        if active_session is not None and active_session.plan_id == plan.id:
            if active_session.checkpoint_id != checkpoint.id:
                raise ValueError("Сначала останови активный таймер у другой темы")
            return await _refresh_plan(session, plan.id)

        plan.status = StudyPlanStatus.ACTIVE.value
        session.add(
            StudySession(
                plan_id=plan.id,
                checkpoint_id=checkpoint.id,
                status=StudySessionStatus.RUNNING.value,
                started_at=current_now,
                progress_percent=0,
            )
        )
        await session.commit()
        return await _refresh_plan(session, plan.id)

    active_session = await get_active_session_for_plan(session, plan.id)
    if active_session is None:
        raise ValueError("Для этого учебного плана нет активного таймера")

    target_checkpoint_id = active_session.checkpoint_id or action.checkpoint_id
    if target_checkpoint_id is None:
        raise ValueError("Не удалось определить тему текущей сессии")
    checkpoint = await get_checkpoint_by_id(session, user.id, target_checkpoint_id)
    if checkpoint is None or checkpoint.plan_id != plan.id:
        raise ValueError("Тема не найдена в выбранном учебном плане")

    if action.action == "pause":
        active_session.status = StudySessionStatus.PAUSED.value
    elif action.action == "stop":
        active_session.status = StudySessionStatus.STOPPED.value
        active_session.progress_percent = _normalize_progress_percent(
            action.progress_percent
        )
        _mark_checkpoint_progress(
            checkpoint,
            active_session.progress_percent,
            current_now,
        )
    else:
        raise ValueError("Неизвестное действие таймера")
    active_session.ended_at = current_now
    await session.commit()
    return await _refresh_plan(session, plan.id)


async def list_sessions(
    session: AsyncSession,
    plan_id: UUID,
) -> list[StudySession]:
    result = await session.execute(
        select(StudySession)
        .where(StudySession.plan_id == plan_id)
        .order_by(StudySession.started_at.desc())
    )
    return list(result.scalars().all())


async def build_plan_response(
    plan: StudyPlan,
    now: datetime | None = None,
) -> StudyPlanResponse:
    current_now = now or _utc_now()
    active_session = next(
        (session for session in plan.sessions if session.ended_at is None), None
    )
    sessions = [
        _session_response(session, current_now)
        for session in sorted(
            plan.sessions, key=lambda value: value.started_at, reverse=True
        )
    ]
    return StudyPlanResponse(
        id=str(plan.id),
        user_id=str(plan.user_id),
        title=plan.title,
        description=plan.description,
        track=StudyPlanTrack(plan.track),
        status=StudyPlanStatus(plan.status),
        total_seconds=_plan_total_seconds(plan, current_now),
        active_session_id=str(active_session.id) if active_session else None,
        active_session_started_at=active_session.started_at if active_session else None,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        modules=[
            StudyModuleResponse(
                id=str(module.id),
                plan_id=str(module.plan_id),
                title=module.title,
                description=module.description,
                order_index=module.order_index,
                created_at=module.created_at,
                updated_at=module.updated_at,
            )
            for module in plan.modules
        ],
        checkpoints=[
            _checkpoint_response(checkpoint) for checkpoint in plan.checkpoints
        ],
        checklist_items=[
            StudyChecklistItemResponse(
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
            for item in plan.checklist_items
        ],
        sessions=sessions,
    )


async def build_weekly_summary(
    session: AsyncSession,
    user: User,
    week_start: date,
    now: datetime | None = None,
) -> StudyWeeklySummaryResponse:
    current_now = now or _utc_now()
    week_end = week_start + timedelta(days=6)
    week_start_dt = datetime.combine(week_start, datetime.min.time(), tzinfo=UTC)
    week_end_exclusive = datetime.combine(
        week_end + timedelta(days=1), datetime.min.time(), tzinfo=UTC
    )
    day_totals: dict[date, dict[str, int]] = {
        week_start + timedelta(days=offset): {"seconds": 0, "sessions": 0}
        for offset in range(7)
    }
    plan_totals: dict[UUID, _WeeklyPlanAggregate] = {}
    completed_checkpoints: list[StudyCheckpointCompletionSummary] = []
    sessions_in_week: list[StudySession] = []

    plans = await list_plans(session, user.id)
    for plan in plans:
        plan_total_seconds = 0
        for study_session in plan.sessions:
            session_end = study_session.ended_at or current_now
            if (
                session_end.date() < week_start
                or study_session.started_at.date() > week_end
            ):
                continue
            clipped_start = max(study_session.started_at, week_start_dt)
            clipped_end = min(session_end, week_end_exclusive)
            if clipped_end <= clipped_start:
                continue
            duration_seconds = int((clipped_end - clipped_start).total_seconds())
            plan_total_seconds += duration_seconds
            sessions_in_week.append(study_session)

            current_day = clipped_start.date()
            while current_day <= clipped_end.date():
                day_start = datetime.combine(
                    current_day, datetime.min.time(), tzinfo=UTC
                )
                day_end = day_start + timedelta(days=1)
                overlap_start = max(clipped_start, day_start)
                overlap_end = min(clipped_end, day_end)
                if overlap_end > overlap_start and current_day in day_totals:
                    day_totals[current_day]["seconds"] += int(
                        (overlap_end - overlap_start).total_seconds()
                    )
                    day_totals[current_day]["sessions"] += 1
                current_day += timedelta(days=1)

        sessions_count = sum(
            1
            for session_item in plan.sessions
            if session_item.started_at.date() <= week_end
            and (session_item.ended_at or current_now).date() >= week_start
        )
        plan_totals[plan.id] = {
            "plan_id": str(plan.id),
            "title": plan.title,
            "total_seconds": plan_total_seconds,
            "sessions_count": sessions_count,
        }
        for checkpoint in plan.checkpoints:
            if (
                checkpoint.completed_at
                and week_start <= checkpoint.completed_at.date() <= week_end
            ):
                completed_checkpoints.append(
                    StudyCheckpointCompletionSummary(
                        checkpoint_id=str(checkpoint.id),
                        plan_id=str(plan.id),
                        plan_title=plan.title,
                        title=checkpoint.title,
                        completed_at=checkpoint.completed_at,
                    )
                )

    sessions_response = [
        _session_response(study_session, current_now)
        for study_session in sorted(
            sessions_in_week, key=lambda value: value.started_at, reverse=True
        )
    ]

    return StudyWeeklySummaryResponse(
        week_start=week_start,
        week_end=week_end,
        total_seconds=sum(item["seconds"] for item in day_totals.values()),
        days=[
            StudyWeeklyDaySummary(
                day=day_value,
                total_seconds=summary["seconds"],
                sessions_count=summary["sessions"],
            )
            for day_value, summary in day_totals.items()
        ],
        plans=[
            StudyWeeklyPlanSummary(
                plan_id=summary["plan_id"],
                title=summary["title"],
                total_seconds=int(summary["total_seconds"]),
                sessions_count=int(summary["sessions_count"]),
            )
            for summary in sorted(
                plan_totals.values(),
                key=lambda item: int(item["total_seconds"]),
                reverse=True,
            )
        ],
        sessions=sessions_response,
        completed_checkpoints=sorted(
            completed_checkpoints,
            key=lambda item: item.completed_at,
            reverse=True,
        ),
    )


async def _refresh_plan(session: AsyncSession, plan_id: UUID) -> StudyPlan:
    # session.get() может вернуть закэшированный экземпляр из identity map без
    # загрузки relationships, что вызывает MissingGreenlet в async-контексте.
    # Явный SELECT с selectinload гарантирует свежую загрузку всех связей.
    result = await session.execute(
        select(StudyPlan)
        .where(StudyPlan.id == plan_id)
        .options(
            selectinload(StudyPlan.checkpoints),
            selectinload(StudyPlan.checklist_items),
            selectinload(StudyPlan.sessions),
        )
    )
    refreshed = result.scalar_one_or_none()
    if refreshed is None:
        raise ValueError("Учебный план не найден")
    return refreshed
