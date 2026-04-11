import { Sidebar } from "@/components/sidebar";
import { getArchiveEntries } from "@/lib/api";
import { formatDateLabel, formatDateTimeLabel } from "@/lib/date-format";
import { requireUser } from "@/lib/auth";

type SearchParams = Record<string, string | string[] | undefined>;

function toSingleValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

function getActivityTypeLabel(activityType: string): string {
  const labels: Record<string, string> = {
    call: "Звонок",
    ticket: "Заявка",
    meeting: "Встреча",
    task: "Задача",
    escalation: "Эскалация",
    other: "Другое",
  };
  return labels[activityType] ?? activityType;
}

export default async function ArchivePage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const params = searchParams ?? {};

  const q = toSingleValue(params.q);
  const activityType = toSingleValue(params.activity_type);
  const externalRef = toSingleValue(params.external_ref);
  const service = toSingleValue(params.service);
  const ticketNumber = toSingleValue(params.ticket_number);
  const dateFrom = toSingleValue(params.date_from);
  const dateTo = toSingleValue(params.date_to);

  const archive = await getArchiveEntries({
    q: q || undefined,
    activity_type: activityType || undefined,
    external_ref: externalRef || undefined,
    service: service || undefined,
    ticket_number: ticketNumber || undefined,
    date_from: dateFrom ? `${dateFrom}T00:00:00Z` : undefined,
    date_to: dateTo ? `${dateTo}T23:59:59Z` : undefined,
    limit: 100,
    offset: 0,
  });
  const entries = archive?.results ?? [];

  return (
    <div className="shell">
      <Sidebar user={user} />

      <aside className="filter-col">
        <div className="filter-col-title">Архив</div>
        <form method="get">
          <div style={{ marginBottom: 20 }}>
            <div className="filter-date-label">Период</div>
            <input type="date" name="date_from" className="filter-date-input" defaultValue={dateFrom} />
            <input type="date" name="date_to" className="filter-date-input" defaultValue={dateTo} />
          </div>

          <div style={{ marginBottom: 20 }}>
            <div className="filter-date-label">Тип активности</div>
            <select name="activity_type" defaultValue={activityType} className="filter-date-input">
              <option value="">Все типы</option>
              <option value="call">Звонок</option>
              <option value="ticket">Заявка</option>
              <option value="meeting">Встреча</option>
              <option value="task">Задача</option>
              <option value="escalation">Эскалация</option>
              <option value="other">Другое</option>
            </select>
          </div>

          <div style={{ marginBottom: 16 }}>
            <div className="filter-date-label">Внешняя ссылка / SR</div>
            <input name="external_ref" className="search-input" placeholder="SR11683266" defaultValue={externalRef} />
          </div>
          <div style={{ marginBottom: 16 }}>
            <div className="filter-date-label">Номер заявки</div>
            <input name="ticket_number" className="search-input" placeholder="SR11683266" defaultValue={ticketNumber} />
          </div>
          <div style={{ marginBottom: 16 }}>
            <div className="filter-date-label">Услуга</div>
            <input name="service" className="search-input" placeholder="TrueConf" defaultValue={service} />
          </div>

          <button className="btn btn-primary" type="submit" style={{ width: "100%" }}>
            Применить фильтры
          </button>
        </form>
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Архив</div>
            <div className="page-sub">История документов, выгрузок и рабочих артефактов</div>
          </div>
          <div className="toolbar">
            <form method="get" style={{ display: "flex", gap: 8 }}>
              <input type="hidden" name="date_from" value={dateFrom} />
              <input type="hidden" name="date_to" value={dateTo} />
              <input type="hidden" name="activity_type" value={activityType} />
              <input type="hidden" name="external_ref" value={externalRef} />
              <input type="hidden" name="service" value={service} />
              <input type="hidden" name="ticket_number" value={ticketNumber} />
              <input name="q" defaultValue={q} className="search-input" placeholder="🔍  Поиск по SR, заявке, устройству..." />
              <button className="btn btn-primary" type="submit">Найти</button>
            </form>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge task">Найдено</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {archive?.total ?? 0}
            </div>
            <div className="page-sub">Архивных записей</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge bgp">Период</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {dateFrom ? formatDateLabel(dateFrom) : "—"}
            </div>
            <div className="page-sub">Начало фильтра</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge acl">Тип</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {activityType || "все"}
            </div>
            <div className="page-sub">Фильтр по активности</div>
          </div>
        </div>

        <div className="section-label">Найдено: {archive?.total ?? 0}</div>
        <div className="plan-list">
          {entries.length === 0 && (
            <div className="plan-item">
              <div className="plan-info">
                <div className="plan-title">Записей не найдено</div>
                <div className="plan-sub">Измени фильтры или период поиска.</div>
              </div>
            </div>
          )}

          {entries.map((entry) => (
            <div key={entry.id} className="plan-item">
              <div className="plan-icon vlan">◫</div>
              <div className="plan-info">
                <div className="plan-title">{entry.title}</div>
                <div className="plan-sub">
                  {formatDateTimeLabel(entry.created_at)} · {formatDateLabel(entry.work_date)} · {getActivityTypeLabel(entry.activity_type)} · {entry.ticket_number ?? "без SR"}
                </div>
                {entry.service && <div className="plan-sub">Услуга: {entry.service}</div>}
                {entry.description && <div className="plan-sub" style={{ marginTop: 4 }}>{entry.description}</div>}
              </div>
              <div className="plan-actions">
                <button className="btn btn-sm">{entry.status}</button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
