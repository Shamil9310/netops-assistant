import { Sidebar } from "@/components/sidebar";
import { PlannedEventConvertButton } from "@/components/planned-event-convert-button";
import { PlannedEventCreateForm } from "@/components/planned-event-create-form";
import { getDayDashboard, getHealth } from "@/lib/api";
import { requireUser } from "@/lib/auth";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function toSingleValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

function getTodayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
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

function labelForStatus(value: string): string {
  const labels: Record<string, string> = {
    open: "Открыта",
    in_progress: "В работе",
    closed: "Закрыта",
    cancelled: "Отменена",
  };
  return labels[value] ?? value;
}

function formatTime(value: string | null): string {
  if (!value) {
    return "—";
  }
  return value.slice(0, 5);
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export default async function HomePage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const resolvedParams = searchParams ? await searchParams : {};
  const selectedWorkDate = toSingleValue(resolvedParams.work_date) || getTodayIsoDate();
  const health = await getHealth();
  const dashboard = await getDayDashboard(selectedWorkDate);

  return (
    <div className="shell">
      <Sidebar user={user} />

      <aside className="filter-col">
        <div className="filter-col-title">День</div>
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
            <span className="filter-stat-label">Ticket</span>
            <span className="filter-stat-val">{dashboard?.activity_counters.ticket ?? 0}</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Task</span>
            <span className="filter-stat-val">{dashboard?.activity_counters.task ?? 0}</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Открыто</span>
            <span className="filter-stat-val">{dashboard?.status_counters.open ?? 0}</span>
          </div>
          <div className="filter-stat-row" style={{ marginTop: 6 }}>
            <span className="filter-stat-label">Backend</span>
            <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, fontWeight: 600 }}>
              <span className="status-dot" />
              {health?.status ?? "offline"}
            </span>
          </div>
        </div>
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Рабочий день</div>
            <div className="page-sub">Реальные данные по work_date: {selectedWorkDate}</div>
          </div>
          <div className="toolbar">
            <a className="btn btn-primary" href={`/journal?work_date=${selectedWorkDate}`}>+ Запись</a>
            <a className="btn" href="/reports">Отчёт</a>
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
                  {labelForActivityType(entry.activity_type)} · {labelForStatus(entry.status)} · {formatTime(entry.started_at)}-{formatTime(entry.ended_at)}
                </div>
                {entry.ticket_number && <div className="plan-sub">Ticket: {entry.ticket_number}</div>}
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
                  {event.event_type} · {formatDateTime(event.scheduled_at)} · completed: {String(event.is_completed)}
                </div>
                {event.external_ref && <div className="plan-sub">Ref: {event.external_ref}</div>}
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
