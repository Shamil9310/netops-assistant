import { Sidebar } from "@/components/sidebar";
import { PlannedEventConvertButton } from "@/components/planned-event-convert-button";
import { PlannedEventCreateForm } from "@/components/planned-event-create-form";
import { getDayDashboard, getHealth } from "@/lib/api";
import { formatDateLabel, formatDateTimeLabel } from "@/lib/date-format";
import { requireUser } from "@/lib/auth";
import { getCurrentWorkDateIso } from "@/lib/work-date";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function toSingleValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

function labelForActivityType(value: string): string {
  const labels: Record<string, string> = {
    call: "Звонок",
    ticket: "Заявка",
    meeting: "Встреча",
    task: "Задача",
    escalation: "Эскалация",
    other: "Прочее",
  };
  return labels[value] ?? value;
}

function labelForPlannedEventType(value: string): string {
  const labels: Record<string, string> = {
    meeting: "Встреча",
    task: "Задача",
    night_work_prep: "Подготовка к ночным работам",
  };
  return labels[value] ?? value;
}

function labelForStatus(value: string): string {
  const labels: Record<string, string> = {
    open: "Открыта",
    in_progress: "В работе",
    closed: "Закрыта",
    cancelled: "Отменена",
  };
  return labels[value] ?? value;
}

function formatClockTime(timeValue: string | null): string {
  if (!timeValue) {
    return "—";
  }
  return timeValue.slice(0, 5);
}

function formatEntryTimeRange(
  workDate: string,
  startedAt: string | null,
  endedAt: string | null,
  endedDate: string | null,
): string {
  const actualEndedDate = endedDate ?? workDate;
  if (workDate === actualEndedDate) {
    return `${formatClockTime(startedAt)}-${formatClockTime(endedAt)}`;
  }
  return `${formatDateLabel(workDate)} ${formatClockTime(startedAt)} -> ${formatDateLabel(actualEndedDate)} ${formatClockTime(endedAt)}`;
}

export default async function TodayPage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const resolvedParams = searchParams ? await searchParams : {};
  const selectedWorkDate = toSingleValue(resolvedParams.work_date) || getCurrentWorkDateIso();
  const health = await getHealth();
  const dashboard = await getDayDashboard(selectedWorkDate);

  return (
    <div className="shell">
      <Sidebar user={user} />

      <aside className="filter-col">
        <div className="filter-col-title">Контроль дня</div>
        <form method="GET">
          <div className="filter-date-label">Рабочая дата</div>
          <input name="work_date" type="date" className="filter-date-input" defaultValue={selectedWorkDate} />
          <button className="btn btn-sm" type="submit">Показать</button>
        </form>

        <div className="filter-divider" />
        <PlannedEventCreateForm initialWorkDate={selectedWorkDate} />

        <div className="filter-divider" />
        <div className="filter-group">
          <div className="filter-group-title">Счётчики</div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Всего</span>
            <span className="filter-stat-val">{dashboard?.activity_counters.total ?? 0}</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Заявки</span>
            <span className="filter-stat-val">{dashboard?.activity_counters.ticket ?? 0}</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Задачи</span>
            <span className="filter-stat-val">{dashboard?.activity_counters.task ?? 0}</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Открыто</span>
            <span className="filter-stat-val">{dashboard?.status_counters.open ?? 0}</span>
          </div>
          <div className="filter-stat-row" style={{ marginTop: 6 }}>
            <span className="filter-stat-label">Бэкенд</span>
            <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, fontWeight: 600 }}>
              <span className="status-dot" />
              {health?.status ?? "недоступен"}
            </span>
          </div>
        </div>
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Сегодня</div>
            <div className="page-sub">Живая лента рабочего дня для выбранной даты: {formatDateLabel(selectedWorkDate)}</div>
          </div>
          <div className="toolbar">
            <a className="btn btn-primary" href={`/journal?work_date=${selectedWorkDate}`}>+ Запись</a>
            <a className="btn" href="/reports">Отчёт</a>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 16,
          }}
        >
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge task">Открыто</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {dashboard?.activity_counters.total ?? 0}
            </div>
            <div className="page-sub">Все записи за смену</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge bgp">Заявки</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {dashboard?.activity_counters.ticket ?? 0}
            </div>
            <div className="page-sub">SR и обращения</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge acl">Задачи</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {dashboard?.activity_counters.task ?? 0}
            </div>
            <div className="page-sub">Рабочие действия</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge maintenance">Backend</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {health?.status ?? "—"}
            </div>
            <div className="page-sub">Состояние API</div>
          </div>
        </div>

        <div className="section-label">Лента дня</div>
        <div className="plan-list">
          {(dashboard?.timeline ?? []).length === 0 && (
            <div className="plan-item">
              <div className="plan-info">
                <div className="plan-title">Записей за выбранную дату нет</div>
                <div className="plan-sub">Создай запись через журнал.</div>
              </div>
            </div>
          )}
          {(dashboard?.timeline ?? []).map((entry) => (
            <div key={entry.id} className="plan-item">
              <div className="plan-icon status">●</div>
              <div className="plan-info">
                <div className="plan-title">{entry.title}</div>
                <div className="plan-sub">
                  {labelForActivityType(entry.activity_type)} · {labelForStatus(entry.status)} · {formatEntryTimeRange(entry.work_date, entry.started_at, entry.ended_at, entry.ended_date)}
                </div>
                {entry.ticket_number && <div className="plan-sub">Заявка: {entry.ticket_number}</div>}
                {entry.service && <div className="plan-sub">Услуга: {entry.service}</div>}
                {entry.description && <div className="plan-sub">{entry.description}</div>}
              </div>
            </div>
          ))}
        </div>

        <div className="section-label">Плановые события дня</div>
        <div className="plan-list">
          {(dashboard?.planned_today ?? []).length === 0 && (
            <div className="plan-item">
              <div className="plan-info">
                <div className="plan-title">Плановых событий нет</div>
                <div className="plan-sub">На эту рабочую дату ещё ничего не запланировано.</div>
              </div>
            </div>
          )}
          {(dashboard?.planned_today ?? []).map((event) => (
            <div key={event.id} className="plan-item">
              <div className="plan-icon plan">◉</div>
              <div className="plan-info">
                <div className="plan-title">{event.title}</div>
                <div className="plan-sub">
                  {labelForPlannedEventType(event.event_type)} · {formatDateTimeLabel(event.scheduled_at)} · завершено: {event.is_completed ? "да" : "нет"}
                </div>
                {event.external_ref && <div className="plan-sub">Ссылка: {event.external_ref}</div>}
                {event.description && <div className="plan-sub">{event.description}</div>}
              </div>
              <div className="plan-actions">
                <PlannedEventConvertButton eventId={event.id} />
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
