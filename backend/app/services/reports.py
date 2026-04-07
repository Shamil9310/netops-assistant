from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.journal import ActivityEntry, ActivityStatus, ActivityType
from app.models.night_work import NightWorkBlock, NightWorkPlan
from app.services.journal import list_entries_for_date

logger = logging.getLogger(__name__)

# Заголовки типов активности на русском — используются в отчётах.
_ACTIVITY_TYPE_LABELS: dict[str, str] = {
    ActivityType.CALL.value: "Звонок",
    ActivityType.TICKET.value: "Заявка",
    ActivityType.MEETING.value: "Встреча",
    ActivityType.TASK.value: "Задача",
    ActivityType.ESCALATION.value: "Эскалация",
    ActivityType.OTHER.value: "Прочее",
}

# Заголовки статусов на русском.
_STATUS_LABELS: dict[str, str] = {
    ActivityStatus.OPEN.value: "Открыта",
    ActivityStatus.IN_PROGRESS.value: "В работе",
    ActivityStatus.CLOSED.value: "Закрыта",
    ActivityStatus.CANCELLED.value: "Отменена",
}

_NIGHT_WORK_STATUS_LABELS: dict[str, str] = {
    "draft": "draft",
    "approved": "approved",
    "in_progress": "in_progress",
    "completed": "completed",
    "cancelled": "cancelled",
    "pending": "pending",
    "failed": "failed",
    "skipped": "skipped",
}

_REPORT_FORMAT_PROFILES: set[str] = {"engineer", "manager"}


def _format_entry(entry: ActivityEntry, index: int) -> str:
    """Форматирует одну запись журнала в строку Markdown.

    Каждая запись — нумерованный пункт с типом, статусом, заголовком и деталями.
    """
    type_label = _ACTIVITY_TYPE_LABELS.get(entry.activity_type, entry.activity_type)
    status_label = _STATUS_LABELS.get(entry.status, entry.status)
    ref_part = f" | ref: `{entry.external_ref}`" if entry.external_ref else ""
    time_part = ""
    if entry.started_at:
        time_part = f" | начало: {entry.started_at.strftime('%H:%M')}"
    if entry.finished_at:
        time_part += f", завершение: {entry.finished_at.strftime('%H:%M')}"

    lines = [f"{index}. **{type_label}** [{status_label}]{ref_part}{time_part}"]
    lines.append(f"   {entry.title}")
    if entry.description:
        lines.append(f"   > {entry.description}")
    return "\n".join(lines)


def _build_summary_section(entries: list[ActivityEntry]) -> str:
    """Формирует раздел итоговой статистики для отчёта."""
    from collections import Counter
    type_counts = Counter(e.activity_type for e in entries)
    status_counts = Counter(e.status for e in entries)

    lines = ["## Итоги\n"]
    lines.append(f"**Всего записей:** {len(entries)}\n")
    lines.append(f"**Суммарное время:** {_format_total_duration(entries)}\n")

    lines.append("**По типам:**")
    for atype, label in _ACTIVITY_TYPE_LABELS.items():
        count = type_counts.get(atype, 0)
        if count:
            lines.append(f"- {label}: {count}")

    lines.append("\n**По статусам:**")
    for status, label in _STATUS_LABELS.items():
        count = status_counts.get(status, 0)
        if count:
            lines.append(f"- {label}: {count}")

    return "\n".join(lines)


def _format_total_duration(entries: list[ActivityEntry]) -> str:
    """Считает суммарное время по записям, где указаны start/finish."""
    total_minutes = 0
    for entry in entries:
        if entry.started_at is None or entry.finished_at is None:
            continue
        delta = entry.finished_at - entry.started_at
        if delta.total_seconds() <= 0:
            continue
        total_minutes += int(delta.total_seconds() // 60)

    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}ч {minutes}м"


async def generate_daily_report(
    session: AsyncSession,
    user_id: UUID,
    report_date: date,
    author_name: str,
) -> str:
    """Генерирует дневной отчёт в формате Markdown.

    Включает все записи журнала за указанный день, сгруппированные
    в хронологическом порядке, плюс итоговую статистику.
    """
    day_start = datetime(report_date.year, report_date.month, report_date.day, 0, 0, 0, tzinfo=UTC)
    day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)

    entries = await list_entries_for_date(session, user_id, day_start, day_end)

    date_str = report_date.strftime("%d.%m.%Y")
    lines = [
        f"# Дневной отчёт — {date_str}",
        f"\n**Сотрудник:** {author_name}",
        f"**Дата:** {date_str}",
        f"**Сформирован:** {datetime.now(UTC).strftime('%d.%m.%Y %H:%M')} UTC\n",
    ]

    if not entries:
        lines.append("_Записей за день не найдено._")
    else:
        lines.append("## Активности\n")
        for i, entry in enumerate(entries, 1):
            lines.append(_format_entry(entry, i))
            lines.append("")
        lines.append(_build_summary_section(entries))

    report = "\n".join(lines)
    logger.info("Сформирован дневной отчёт: user_id=%s, date=%s", user_id, report_date)
    return report


async def generate_weekly_report(
    session: AsyncSession,
    user_id: UUID,
    week_start: date,
    author_name: str,
) -> str:
    """Генерирует недельный отчёт в формате Markdown.

    Охватывает 7 дней начиная с week_start.
    Внутри группирует записи по дням для удобного чтения.
    """
    week_end = week_start + timedelta(days=6)
    range_start = datetime(week_start.year, week_start.month, week_start.day, 0, 0, 0, tzinfo=UTC)
    range_end = datetime(week_end.year, week_end.month, week_end.day, 23, 59, 59, tzinfo=UTC)

    entries = await list_entries_for_date(session, user_id, range_start, range_end)

    start_str = week_start.strftime("%d.%m.%Y")
    end_str = week_end.strftime("%d.%m.%Y")

    lines = [
        f"# Недельный отчёт — {start_str} – {end_str}",
        f"\n**Сотрудник:** {author_name}",
        f"**Период:** {start_str} – {end_str}",
        f"**Сформирован:** {datetime.now(UTC).strftime('%d.%m.%Y %H:%M')} UTC\n",
    ]

    if not entries:
        lines.append("_Записей за период не найдено._")
    else:
        # Группируем по дням.
        days: dict[date, list[ActivityEntry]] = {}
        for entry in entries:
            entry_date = entry.work_date
            days.setdefault(entry_date, []).append(entry)

        for day in sorted(days.keys()):
            day_entries = days[day]
            lines.append(f"## {day.strftime('%d.%m.%Y (%A)')}\n")
            for i, entry in enumerate(day_entries, 1):
                lines.append(_format_entry(entry, i))
                lines.append("")

        lines.append(_build_summary_section(entries))

    report = "\n".join(lines)
    logger.info("Сформирован недельный отчёт: user_id=%s, week_start=%s", user_id, week_start)
    return report


async def generate_range_report(
    session: AsyncSession,
    user_id: UUID,
    date_from: date,
    date_to: date,
    author_name: str,
) -> str:
    """Генерирует отчёт за произвольный период в формате Markdown.

    Аналог weekly report, но с произвольными датами начала и конца.
    Группирует записи по дням внутри периода.
    """
    range_start = datetime(date_from.year, date_from.month, date_from.day, 0, 0, 0, tzinfo=UTC)
    range_end = datetime(date_to.year, date_to.month, date_to.day, 23, 59, 59, tzinfo=UTC)

    entries = await list_entries_for_date(session, user_id, range_start, range_end)

    from_str = date_from.strftime("%d.%m.%Y")
    to_str = date_to.strftime("%d.%m.%Y")

    lines = [
        f"# Отчёт за период — {from_str} – {to_str}",
        f"\n**Сотрудник:** {author_name}",
        f"**Период:** {from_str} – {to_str}",
        f"**Сформирован:** {datetime.now(UTC).strftime('%d.%m.%Y %H:%M')} UTC\n",
    ]

    if not entries:
        lines.append("_Записей за период не найдено._")
    else:
        days: dict[date, list[ActivityEntry]] = {}
        for entry in entries:
            entry_date = entry.work_date
            days.setdefault(entry_date, []).append(entry)

        for day in sorted(days.keys()):
            day_entries = days[day]
            lines.append(f"## {day.strftime('%d.%m.%Y')}\n")
            for i, entry in enumerate(day_entries, 1):
                lines.append(_format_entry(entry, i))
                lines.append("")

        lines.append(_build_summary_section(entries))

    report = "\n".join(lines)
    logger.info("Сформирован отчёт за период: user_id=%s, %s – %s", user_id, date_from, date_to)
    return report


def _build_night_work_follow_up_summary(plan: NightWorkPlan) -> str:
    """Формирует краткий утренний summary по результатам ночного окна."""
    total_blocks = len(plan.blocks)
    total_steps = sum(len(block.steps) for block in plan.blocks)
    failed_blocks = sum(1 for block in plan.blocks if block.status in {"failed", "blocked"})
    failed_steps = sum(1 for block in plan.blocks for step in block.steps if step.status in {"failed", "blocked"})
    completed_steps = sum(1 for block in plan.blocks for step in block.steps if step.status == "completed")
    deferred_steps = sum(1 for block in plan.blocks for step in block.steps if step.status == "skipped")
    handed_off_steps = sum(
        1
        for block in plan.blocks
        for step in block.steps
        if bool(getattr(step, "handoff_to", None))
    )

    return (
        f"Итог ночных работ: {plan.title}\n"
        f"Статус плана: {_NIGHT_WORK_STATUS_LABELS.get(plan.status, plan.status)}\n"
        f"Блоков: {total_blocks}, Шагов: {total_steps}, Выполнено: {completed_steps}, "
        f"Не выполнено: {failed_steps}, Перенесено: {deferred_steps}, Передано: {handed_off_steps}, "
        f"Проблемных блоков: {failed_blocks}"
    )


def _build_night_work_report(plan: NightWorkPlan, author_name: str) -> str:
    """Формирует markdown-отчёт по ночным работам на основе фактического исполнения."""
    lines = [
        f"# Итог ночных работ — {plan.title}",
        f"\n**Сотрудник:** {author_name}",
        f"**Статус плана:** {_NIGHT_WORK_STATUS_LABELS.get(plan.status, plan.status)}",
        f"**Плановое время:** {plan.scheduled_at.isoformat() if plan.scheduled_at else 'не задано'}",
        f"**Факт старта:** {plan.started_at.isoformat() if plan.started_at else 'не задан'}",
        f"**Факт завершения:** {plan.finished_at.isoformat() if plan.finished_at else 'не задан'}\n",
    ]

    if plan.description:
        lines.append("## Описание\n")
        lines.append(plan.description)
        lines.append("")

    lines.append("## Блоки исполнения\n")
    if not plan.blocks:
        lines.append("_Блоки отсутствуют._")
    else:
        for block_index, block in enumerate(plan.blocks, 1):
            lines.append(
                f"### {block_index}. {block.title} "
                f"(SR: {block.sr_number or '—'}, status: {_NIGHT_WORK_STATUS_LABELS.get(block.status, block.status)})"
            )
            if block.description:
                lines.append(block.description)
            if block.result_comment:
                lines.append(f"> Комментарий: {block.result_comment}")

            if not block.steps:
                lines.append("- Шаги отсутствуют")
                lines.append("")
                continue

            for step_index, step in enumerate(block.steps, 1):
                flags: list[str] = []
                if step.is_rollback:
                    flags.append("rollback")
                if step.is_post_action:
                    flags.append("post-action")
                flags_text = f" ({', '.join(flags)})" if flags else ""
                lines.append(
                    f"- {step_index}. {step.title}{flags_text} "
                    f"[{_NIGHT_WORK_STATUS_LABELS.get(step.status, step.status)}]"
                )
                if step.description:
                    lines.append(f"  - План: {step.description}")
                if step.actual_result:
                    lines.append(f"  - Факт: {step.actual_result}")
                if step.executor_comment:
                    lines.append(f"  - Комментарий: {step.executor_comment}")
                if step.collaborators:
                    lines.append(f"  - Совместно с: {', '.join(step.collaborators)}")
                if step.handoff_to:
                    lines.append(f"  - Передано в: {step.handoff_to}")
            lines.append("")

    lines.append("## Morning follow-up summary\n")
    lines.append(_build_night_work_follow_up_summary(plan))
    return "\n".join(lines)


async def _save_follow_up_entry(session: AsyncSession, plan: NightWorkPlan, summary: str) -> None:
    """Сохраняет follow-up результат ночных работ в дневной журнал."""
    first_sr_number = next((block.sr_number for block in plan.blocks if block.sr_number), None)
    journal_entry = ActivityEntry(
        user_id=plan.user_id,
        work_date=(plan.started_at or datetime.now(UTC)).date(),
        activity_type=ActivityType.TASK.value,
        status=ActivityStatus.CLOSED.value,
        title=f"Follow-up после ночных работ: {plan.title}",
        description=summary,
        external_ref=first_sr_number,
        ticket_number=first_sr_number,
        started_at=plan.started_at,
        finished_at=plan.finished_at,
    )
    session.add(journal_entry)
    await session.commit()


async def generate_night_work_result_report(
    session: AsyncSession,
    user_id: UUID,
    plan_id: UUID,
    author_name: str,
) -> str:
    """Генерирует итоговый отчёт по ночным работам и создаёт follow-up запись в журнале."""
    result = await session.execute(
        select(NightWorkPlan)
        .where(NightWorkPlan.id == plan_id)
        .where(NightWorkPlan.user_id == user_id)
        .options(selectinload(NightWorkPlan.blocks).selectinload(NightWorkBlock.steps))
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise ValueError("План ночных работ не найден")

    report = _build_night_work_report(plan, author_name)
    summary = _build_night_work_follow_up_summary(plan)
    await _save_follow_up_entry(session, plan, summary)
    logger.info("Сформирован итоговый отчёт ночных работ: user_id=%s, plan_id=%s", user_id, plan_id)
    return report


def format_report_content(content_md: str, profile: str) -> str:
    """Применяет формат-профиль отчёта (engineer/manager)."""
    if profile not in _REPORT_FORMAT_PROFILES:
        raise ValueError(f"Недопустимый format_profile: {profile}")
    if profile == "engineer":
        return content_md
    return _to_manager_format(content_md)


def _to_manager_format(content_md: str) -> str:
    """Упрощает документ до руководительского формата (без детальных шагов)."""
    lines = content_md.splitlines()
    result: list[str] = []
    summary_started = False

    for line in lines:
        if line.startswith("# "):
            result.append(line)
            continue
        if "## Итоги" in line or "## Morning follow-up summary" in line:
            summary_started = True
            result.append(line)
            continue
        if summary_started:
            if line.startswith("## ") and "Итоги" not in line and "Morning follow-up summary" not in line:
                summary_started = False
                continue
            result.append(line)

    if len(result) <= 1:
        header = lines[0] if lines else "# Отчёт"
        return "\n".join([header, "", "_Executive summary недоступен для выбранного документа._"])
    return "\n".join(result)
