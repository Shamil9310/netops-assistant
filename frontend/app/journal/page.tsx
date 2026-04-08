import { Sidebar } from "@/components/sidebar";
import { JournalCreateForm } from "@/components/journal-create-form";
import { JournalDateFilter } from "@/components/journal-date-filter";
import { JournalEntryActions } from "@/components/journal-entry-actions";
import { getJournalEntries } from "@/lib/api";
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

export default async function JournalPage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const resolvedParams = searchParams ? await searchParams : {};
  const selectedWorkDate = toSingleValue(resolvedParams.work_date) || getTodayIsoDate();
  const journal = await getJournalEntries(selectedWorkDate);
  const items = journal?.items ?? [];
  const lastEndedAtRaw = [...items].reverse().find((item) => item.ended_at)?.ended_at ?? null;
  const lastEndedAt = lastEndedAtRaw ? lastEndedAtRaw.slice(0, 5) : null;

  return (
    <div className="shell">
      <Sidebar user={user} />

      <aside className="filter-col">
        <div className="filter-col-title">Журнал</div>
        <JournalCreateForm key={selectedWorkDate} initialWorkDate={selectedWorkDate} lastEndedAt={lastEndedAt} />
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Журнал</div>
            <div className="page-sub">Записи за рабочую дату {selectedWorkDate}</div>
          </div>
          <div className="toolbar">
            <JournalDateFilter initialDate={selectedWorkDate} />
          </div>
        </div>

        <div className="section-label">Записей: {items.length}</div>
        <div className="plan-list">
          {items.length === 0 && (
            <div className="plan-item">
              <div className="plan-info">
                <div className="plan-title">Нет записей за выбранную дату</div>
                <div className="plan-sub">Создай первую запись через форму слева.</div>
              </div>
            </div>
          )}

          {items.map((item) => (
            <div key={item.id} className="plan-item">
              <div className="plan-icon status">●</div>
              <div className="plan-info">
                <div className="plan-title">{item.title}</div>
                <div className="plan-sub">
                  {labelForActivityType(item.activity_type)} · {labelForStatus(item.status)} · {formatTime(item.started_at)}-{formatTime(item.ended_at)}
                </div>
                {item.is_backdated && <div className="plan-sub">Добавлено задним числом</div>}
                {item.ticket_number && <div className="plan-sub">Ticket: {item.ticket_number}</div>}
                {item.task_url && (
                  <div className="plan-sub">
                    <a href={item.task_url} target="_blank" rel="noreferrer">
                      Открыть задачу
                    </a>
                  </div>
                )}
                {item.description && <div className="plan-sub">{item.description}</div>}
                {item.resolution && <div className="plan-sub"><strong>Решение:</strong> {item.resolution}</div>}
              </div>
              <div className="plan-actions">
                <JournalEntryActions
                  entryId={item.id}
                  ticketNumber={item.ticket_number}
                  activityType={item.activity_type}
                  status={item.status}
                  startedAt={item.started_at}
                  endedAt={item.ended_at}
                  currentDescription={item.description}
                  currentResolution={item.resolution}
                  currentContact={item.contact}
                  currentTaskUrl={item.task_url}
                />
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
