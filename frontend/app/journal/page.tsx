import { Sidebar } from "@/components/sidebar";
import { JournalCreateForm } from "@/components/journal-create-form";
import { JournalEntryActions } from "@/components/journal-entry-actions";
import { getJournalEntries } from "@/lib/api";
import { requireUser } from "@/lib/auth";

type SearchParams = Record<string, string | string[] | undefined>;

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
  const selectedWorkDate = toSingleValue(searchParams?.work_date) || getTodayIsoDate();
  const journal = await getJournalEntries(selectedWorkDate);
  const items = journal?.items ?? [];

  return (
    <div className="shell">
      <Sidebar user={user} />

      <aside className="filter-col">
        <div className="filter-col-title">Журнал</div>
        <JournalCreateForm initialWorkDate={selectedWorkDate} />
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Журнал</div>
            <div className="page-sub">Записи за рабочую дату {selectedWorkDate}</div>
          </div>
          <div className="toolbar">
            <form method="GET">
              <input name="work_date" type="date" className="filter-date-input" defaultValue={selectedWorkDate} />
              <button className="btn btn-sm" type="submit">Показать</button>
            </form>
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
                {item.description && <div className="plan-sub">{item.description}</div>}
              </div>
              <div className="plan-actions">
                <JournalEntryActions
                  entryId={item.id}
                  currentTitle={item.title}
                  currentDescription={item.description}
                />
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
