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
  return `${workDate} ${formatClockTime(startedAt)} -> ${actualEndedDate} ${formatClockTime(endedAt)}`;
}

export default async function JournalPage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const resolvedParams = searchParams ? await searchParams : {};
  const selectedWorkDate = toSingleValue(resolvedParams.work_date) || getTodayIsoDate();
  const journalEntriesResponse = await getJournalEntries(selectedWorkDate);
  const journalEntries = journalEntriesResponse?.items ?? [];
  const latestEndedAtValue =
    [...journalEntries].reverse().find((entry) => entry.ended_at)?.ended_at ?? null;
  const lastEndedAt = latestEndedAtValue ? latestEndedAtValue.slice(0, 5) : null;

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

        <div className="section-label">Записей: {journalEntries.length}</div>
        <div className="plan-list">
          {journalEntries.length === 0 && (
            <div className="plan-item">
              <div className="plan-info">
                <div className="plan-title">Нет записей за выбранную дату</div>
                <div className="plan-sub">Создай первую запись через форму слева.</div>
              </div>
            </div>
          )}

          {journalEntries.map((entry) => (
            <div key={entry.id} className="plan-item">
              <div className="plan-icon status">●</div>
              <div className="plan-info">
                <div className="plan-title">{entry.title}</div>
                <div className="plan-sub">
                  {labelForActivityType(entry.activity_type)} · {labelForStatus(entry.status)} · {formatEntryTimeRange(entry.work_date, entry.started_at, entry.ended_at, entry.ended_date)}
                </div>
                {entry.is_backdated && <div className="plan-sub">Добавлено задним числом</div>}
                {entry.ticket_number && <div className="plan-sub">Заявка: {entry.ticket_number}</div>}
                {entry.task_url && (
                  <div className="plan-sub">
                    <a href={entry.task_url} target="_blank" rel="noreferrer">
                      Открыть задачу
                    </a>
                  </div>
                )}
                {entry.description && <div className="plan-sub">{entry.description}</div>}
                {entry.resolution && <div className="plan-sub"><strong>Решение:</strong> {entry.resolution}</div>}
              </div>
              <div className="plan-actions">
                <JournalEntryActions
                  entryId={entry.id}
                  ticketNumber={entry.ticket_number}
                  activityType={entry.activity_type}
                  status={entry.status}
                  workDate={entry.work_date}
                  startedAt={entry.started_at}
                  endedAt={entry.ended_at}
                  endedDate={entry.ended_date}
                  currentDescription={entry.description}
                  currentResolution={entry.resolution}
                  currentContact={entry.contact}
                  currentTaskUrl={entry.task_url}
                />
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
