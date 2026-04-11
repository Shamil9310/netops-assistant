from __future__ import annotations

import logging
from enum import StrEnum
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.night_work import (
    NightWorkBlock,
    NightWorkBlockStatus,
    NightWorkPlan,
    NightWorkPlanStatus,
    NightWorkStep,
    NightWorkStepStatus,
)
from app.models.template import PlanTemplate

logger = logging.getLogger(__name__)

_PLAN_ALLOWED_TRANSITIONS: dict[NightWorkPlanStatus, set[NightWorkPlanStatus]] = {
    NightWorkPlanStatus.DRAFT: {
        NightWorkPlanStatus.APPROVED,
        NightWorkPlanStatus.CANCELLED,
    },
    NightWorkPlanStatus.APPROVED: {
        NightWorkPlanStatus.IN_PROGRESS,
        NightWorkPlanStatus.CANCELLED,
    },
    NightWorkPlanStatus.IN_PROGRESS: {
        NightWorkPlanStatus.COMPLETED,
        NightWorkPlanStatus.CANCELLED,
    },
    NightWorkPlanStatus.COMPLETED: set(),
    NightWorkPlanStatus.CANCELLED: set(),
}

_BLOCK_ALLOWED_TRANSITIONS: dict[NightWorkBlockStatus, set[NightWorkBlockStatus]] = {
    NightWorkBlockStatus.PENDING: {
        NightWorkBlockStatus.IN_PROGRESS,
        NightWorkBlockStatus.SKIPPED,
        NightWorkBlockStatus.FAILED,
        NightWorkBlockStatus.BLOCKED,
    },
    NightWorkBlockStatus.IN_PROGRESS: {
        NightWorkBlockStatus.COMPLETED,
        NightWorkBlockStatus.FAILED,
        NightWorkBlockStatus.SKIPPED,
        NightWorkBlockStatus.BLOCKED,
    },
    NightWorkBlockStatus.BLOCKED: {
        NightWorkBlockStatus.IN_PROGRESS,
        NightWorkBlockStatus.SKIPPED,
        NightWorkBlockStatus.FAILED,
    },
    NightWorkBlockStatus.COMPLETED: set(),
    NightWorkBlockStatus.FAILED: set(),
    NightWorkBlockStatus.SKIPPED: set(),
}

_STEP_ALLOWED_TRANSITIONS: dict[NightWorkStepStatus, set[NightWorkStepStatus]] = {
    NightWorkStepStatus.PENDING: {
        NightWorkStepStatus.IN_PROGRESS,
        NightWorkStepStatus.SKIPPED,
        NightWorkStepStatus.FAILED,
        NightWorkStepStatus.BLOCKED,
    },
    NightWorkStepStatus.IN_PROGRESS: {
        NightWorkStepStatus.COMPLETED,
        NightWorkStepStatus.FAILED,
        NightWorkStepStatus.SKIPPED,
        NightWorkStepStatus.BLOCKED,
    },
    NightWorkStepStatus.BLOCKED: {
        NightWorkStepStatus.IN_PROGRESS,
        NightWorkStepStatus.SKIPPED,
        NightWorkStepStatus.FAILED,
    },
    NightWorkStepStatus.COMPLETED: set(),
    NightWorkStepStatus.FAILED: set(),
    NightWorkStepStatus.SKIPPED: set(),
}


def _validate_transition[T: StrEnum](
    current_status: T, next_status: T, allowed: dict[T, set[T]], object_name: str
) -> None:
    """Проверяет, допустим ли переход статуса для сущности.

    Бизнес-логика:
    - запрещаем "скачки" через этапы, чтобы не терять историю исполнения;
    - запрещаем изменения после terminal-статусов;
    - разрешаем idempotent-вызовы (переход в тот же статус) для безопасных ретраев.
    """
    if current_status == next_status:
        return

    allowed_targets = allowed.get(current_status, set())
    if next_status not in allowed_targets:
        raise ValueError(
            f"Недопустимый переход статуса {object_name}: "
            f"{current_status.value} -> {next_status.value}"
        )


def _resolve_started_at(
    current_started_at: datetime | None,
    started_at_from_request: datetime | None,
    new_status_value: str,
) -> datetime | None:
    """Определяет started_at для статусов выполнения.

    Если статус становится IN_PROGRESS и время не передано явно, проставляем now(UTC),
    чтобы у плана/блока/шага был фиксированный момент старта.
    """
    if started_at_from_request is not None:
        return started_at_from_request
    if new_status_value == "in_progress" and current_started_at is None:
        return datetime.now(UTC)
    return current_started_at


def _resolve_finished_at(
    current_finished_at: datetime | None,
    finished_at_from_request: datetime | None,
    new_status_value: str,
) -> datetime | None:
    """Определяет finished_at для конечных статусов исполнения."""
    terminal_statuses = {"completed", "failed", "skipped", "blocked", "cancelled"}
    if finished_at_from_request is not None:
        return finished_at_from_request
    if new_status_value in terminal_statuses and current_finished_at is None:
        return datetime.now(UTC)
    return current_finished_at


# ---------------------------------------------------------------------------
# Планы
# ---------------------------------------------------------------------------


async def list_plans(
    session: AsyncSession,
    user_id: UUID,
    status: NightWorkPlanStatus | None = None,
) -> list[NightWorkPlan]:
    """Возвращает планы ночных работ пользователя с фильтром по статусу."""
    query = (
        select(NightWorkPlan)
        .where(NightWorkPlan.user_id == user_id)
        .options(selectinload(NightWorkPlan.blocks).selectinload(NightWorkBlock.steps))
        .order_by(NightWorkPlan.created_at.desc())
    )
    if status is not None:
        query = query.where(NightWorkPlan.status == status.value)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_plan_by_id(
    session: AsyncSession, plan_id: UUID, user_id: UUID
) -> NightWorkPlan | None:
    """Возвращает план по ID, только если он принадлежит пользователю (IDOR-защита)."""
    result = await session.execute(
        select(NightWorkPlan)
        .where(NightWorkPlan.id == plan_id)
        .where(NightWorkPlan.user_id == user_id)
        .options(selectinload(NightWorkPlan.blocks).selectinload(NightWorkBlock.steps))
    )
    return result.scalar_one_or_none()


async def create_plan(
    session: AsyncSession,
    user_id: UUID,
    title: str,
    description: str | None,
    scheduled_at: datetime | None,
    participants: list[str] | None = None,
) -> NightWorkPlan:
    """Создаёт новый план ночных работ в статусе DRAFT."""
    plan = NightWorkPlan(
        user_id=user_id,
        title=title,
        description=description,
        scheduled_at=scheduled_at,
        participants=_normalize_participants(participants),
        status=NightWorkPlanStatus.DRAFT.value,
    )
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    logger.info("Создан план ночных работ: id=%s, user_id=%s", plan.id, user_id)
    return plan


async def update_plan_status(
    session: AsyncSession,
    plan: NightWorkPlan,
    new_status: NightWorkPlanStatus,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> NightWorkPlan:
    """Обновляет статус плана.

    Переход статусов: DRAFT → APPROVED → IN_PROGRESS → COMPLETED / CANCELLED.
    started_at и finished_at заполняются автоматически при переходе в IN_PROGRESS и COMPLETED.
    """
    current_status = NightWorkPlanStatus(plan.status)
    _validate_transition(current_status, new_status, _PLAN_ALLOWED_TRANSITIONS, "плана")

    plan.status = new_status.value
    plan.started_at = _resolve_started_at(plan.started_at, started_at, new_status.value)
    plan.finished_at = _resolve_finished_at(
        plan.finished_at, finished_at, new_status.value
    )
    await session.commit()
    await session.refresh(plan)
    logger.info("Статус плана %s изменён на %s", plan.id, new_status)
    return plan


async def update_plan(
    session: AsyncSession,
    plan: NightWorkPlan,
    title: str | None,
    description: str | None,
    scheduled_at: datetime | None,
    participants: list[str] | None,
) -> NightWorkPlan:
    """Обновляет поля плана (только в статусе DRAFT)."""
    if title is not None:
        plan.title = title
    if description is not None:
        plan.description = description
    if scheduled_at is not None:
        plan.scheduled_at = scheduled_at
    if participants is not None:
        plan.participants = _normalize_participants(participants)
    await session.commit()
    await session.refresh(plan)
    return plan


async def delete_plan(session: AsyncSession, plan: NightWorkPlan) -> None:
    """Удаляет план (только DRAFT или CANCELLED)."""
    await session.delete(plan)
    await session.commit()
    logger.info("Удалён план ночных работ: id=%s", plan.id)


# ---------------------------------------------------------------------------
# Блоки (SR)
# ---------------------------------------------------------------------------


async def add_block(
    session: AsyncSession,
    plan: NightWorkPlan,
    title: str,
    description: str | None,
    sr_number: str | None,
    order_index: int,
) -> NightWorkBlock:
    """Добавляет новый блок (SR/изменение) в план."""
    block = NightWorkBlock(
        plan_id=plan.id,
        title=title,
        description=description,
        sr_number=sr_number,
        order_index=order_index,
        status=NightWorkBlockStatus.PENDING.value,
    )
    session.add(block)
    await session.commit()
    await session.refresh(block)
    return block


async def get_block_by_id(
    session: AsyncSession, block_id: UUID, plan_id: UUID
) -> NightWorkBlock | None:
    """Возвращает блок по ID, только если он принадлежит указанному плану."""
    result = await session.execute(
        select(NightWorkBlock)
        .where(NightWorkBlock.id == block_id)
        .where(NightWorkBlock.plan_id == plan_id)
        .options(selectinload(NightWorkBlock.steps))
    )
    return result.scalar_one_or_none()


async def update_block_status(
    session: AsyncSession,
    block: NightWorkBlock,
    new_status: NightWorkBlockStatus,
    result_comment: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> NightWorkBlock:
    """Обновляет статус блока."""
    current_status = NightWorkBlockStatus(block.status)
    _validate_transition(
        current_status, new_status, _BLOCK_ALLOWED_TRANSITIONS, "блока"
    )

    block.status = new_status.value
    if result_comment is not None:
        block.result_comment = result_comment
    block.started_at = _resolve_started_at(
        block.started_at, started_at, new_status.value
    )
    block.finished_at = _resolve_finished_at(
        block.finished_at, finished_at, new_status.value
    )
    await session.commit()
    await session.refresh(block)
    return block


async def update_block(
    session: AsyncSession,
    block: NightWorkBlock,
    title: str | None,
    description: str | None,
    sr_number: str | None,
    order_index: int | None,
) -> NightWorkBlock:
    """Обновляет поля блока."""
    if title is not None:
        block.title = title
    if description is not None:
        block.description = description
    if sr_number is not None:
        block.sr_number = sr_number.strip() or None
    if order_index is not None:
        block.order_index = order_index
    await session.commit()
    await session.refresh(block)
    return block


# ---------------------------------------------------------------------------
# Шаги
# ---------------------------------------------------------------------------


async def add_step(
    session: AsyncSession,
    block: NightWorkBlock,
    title: str,
    description: str | None,
    order_index: int,
    is_rollback: bool,
    is_post_action: bool,
) -> NightWorkStep:
    """Добавляет новый шаг в блок."""
    step = NightWorkStep(
        block_id=block.id,
        title=title,
        description=description,
        order_index=order_index,
        is_rollback=is_rollback,
        is_post_action=is_post_action,
        status=NightWorkStepStatus.PENDING.value,
    )
    session.add(step)
    await session.commit()
    await session.refresh(step)
    return step


async def get_step_by_id(
    session: AsyncSession, step_id: UUID, block_id: UUID
) -> NightWorkStep | None:
    """Возвращает шаг по ID, только если он принадлежит указанному блоку."""
    result = await session.execute(
        select(NightWorkStep)
        .where(NightWorkStep.id == step_id)
        .where(NightWorkStep.block_id == block_id)
    )
    return result.scalar_one_or_none()


async def update_step_status(
    session: AsyncSession,
    step: NightWorkStep,
    new_status: NightWorkStepStatus,
    actual_result: str | None = None,
    executor_comment: str | None = None,
    collaborators: list[str] | None = None,
    handoff_to: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> NightWorkStep:
    """Обновляет статус шага и фиксирует фактический результат."""
    current_status = NightWorkStepStatus(step.status)
    _validate_transition(current_status, new_status, _STEP_ALLOWED_TRANSITIONS, "шага")

    step.status = new_status.value
    if actual_result is not None:
        step.actual_result = actual_result
    if executor_comment is not None:
        step.executor_comment = executor_comment
    if collaborators is not None:
        step.collaborators = _normalize_participants(collaborators)
    if handoff_to is not None:
        step.handoff_to = handoff_to.strip() or None
    step.started_at = _resolve_started_at(step.started_at, started_at, new_status.value)
    step.finished_at = _resolve_finished_at(
        step.finished_at, finished_at, new_status.value
    )
    await session.commit()
    await session.refresh(step)
    return step


async def update_step(
    session: AsyncSession,
    step: NightWorkStep,
    title: str | None,
    description: str | None,
    order_index: int | None,
    is_rollback: bool | None,
    is_post_action: bool | None,
) -> NightWorkStep:
    """Обновляет поля шага."""
    if title is not None:
        step.title = title
    if description is not None:
        step.description = description
    if order_index is not None:
        step.order_index = order_index
    if is_rollback is not None:
        step.is_rollback = is_rollback
    if is_post_action is not None:
        step.is_post_action = is_post_action
    await session.commit()
    await session.refresh(step)
    return step


def render_template_text(text: str | None, variables: dict[str, str]) -> str | None:
    """Подставляет переменные в текст вида {{variable_name}}."""
    if text is None:
        return None

    rendered = text
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


async def create_plan_from_template(
    session: AsyncSession,
    user_id: UUID,
    template: PlanTemplate,
    variables: dict[str, str],
    title: str | None = None,
    scheduled_at: datetime | None = None,
) -> NightWorkPlan:
    """Создаёт план ночных работ на основе данных шаблона."""
    blocks_payload = template.template_payload.get("blocks")
    if blocks_payload is not None and not isinstance(blocks_payload, list):
        raise ValueError("Поле template_payload.blocks должно быть списком")

    plan_title = (
        render_template_text(title or template.name, variables) or template.name
    )
    plan_description = render_template_text(template.description, variables)

    plan = NightWorkPlan(
        user_id=user_id,
        title=plan_title,
        description=plan_description,
        scheduled_at=scheduled_at,
        participants=[],
        status=NightWorkPlanStatus.DRAFT.value,
    )
    session.add(plan)
    await session.flush()

    for block_index, raw_block in enumerate(blocks_payload or []):
        if not isinstance(raw_block, dict):
            raise ValueError(
                "Каждый элемент в template_payload.blocks должен быть объектом"
            )

        block_title = (
            render_template_text(
                str(raw_block.get("title", f"Block {block_index + 1}")), variables
            )
            or f"Block {block_index + 1}"
        )
        block_description = render_template_text(
            (
                raw_block.get("description")
                if isinstance(raw_block.get("description"), str)
                else None
            ),
            variables,
        )
        block_sr_number = render_template_text(
            (
                raw_block.get("sr_number")
                if isinstance(raw_block.get("sr_number"), str)
                else None
            ),
            variables,
        )

        block = NightWorkBlock(
            plan_id=plan.id,
            title=block_title,
            description=block_description,
            sr_number=block_sr_number,
            order_index=block_index,
            status=NightWorkBlockStatus.PENDING.value,
        )
        session.add(block)
        await session.flush()

        steps_payload = raw_block.get("steps", [])
        if not isinstance(steps_payload, list):
            raise ValueError("block.steps должен быть списком")

        for step_index, raw_step in enumerate(steps_payload):
            if not isinstance(raw_step, dict):
                raise ValueError("Каждый step в block.steps должен быть объектом")

            step_title = (
                render_template_text(
                    str(raw_step.get("title", f"Step {step_index + 1}")),
                    variables,
                )
                or f"Step {step_index + 1}"
            )
            step_description = render_template_text(
                (
                    raw_step.get("description")
                    if isinstance(raw_step.get("description"), str)
                    else None
                ),
                variables,
            )
            is_rollback = bool(raw_step.get("is_rollback", False))
            is_post_action = bool(raw_step.get("is_post_action", False))

            step = NightWorkStep(
                block_id=block.id,
                title=step_title,
                description=step_description,
                order_index=step_index,
                status=NightWorkStepStatus.PENDING.value,
                is_rollback=is_rollback,
                is_post_action=is_post_action,
            )
            session.add(step)

    await session.commit()
    await session.refresh(plan)
    logger.info(
        "Создан план из шаблона: plan_id=%s, template_key=%s", plan.id, template.key
    )
    return plan


def _normalize_participants(participants: list[str] | None) -> list[str]:
    """Нормализует список участников окна: trim + удаление пустых дублей."""
    if not participants:
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for item in participants:
        value = item.strip()
        if not value:
            continue
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(value)
    return normalized
