import { Sidebar } from "@/components/sidebar";
import { JournalCreateForm } from "@/components/journal-create-form";
import { JournalDateFilter } from "@/components/journal-date-filter";
import { JournalDeduplicateButton } from "@/components/journal-deduplicate-button";
import { JournalBulkDeleteControls } from "@/components/journal-bulk-delete-controls";
import { JournalEntrySelectionList } from "@/components/journal-entry-selection-list";
import { getJournalEntries } from "@/lib/api";
import type { JournalEntry } from "@/lib/api";
import { formatDateLabel } from "@/lib/date-format";
import { requireUser } from "@/lib/auth";
import { getCurrentWorkDateIso } from "@/lib/work-date";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function toSingleValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

export default async function JournalPage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const resolvedParams = searchParams ? await searchParams : {};
  const selectedWorkDate = toSingleValue(resolvedParams.work_date) || getCurrentWorkDateIso();
  const journalEntriesResponse = await getJournalEntries(selectedWorkDate);
  const journalEntries = journalEntriesResponse?.items ?? [];
  const isJournalUnavailable = journalEntriesResponse === null;
  const duplicateCount = calculateDuplicateCount(journalEntries);

  return (
    <div className="shell">
      <Sidebar user={user} />

      <aside className="filter-col">
        <div className="filter-col-title">Журнал</div>
        <JournalCreateForm key={selectedWorkDate} initialWorkDate={selectedWorkDate} />
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Журнал</div>
            <div className="page-sub">Записи за рабочую дату {formatDateLabel(selectedWorkDate)}</div>
          </div>
          <div className="toolbar">
            <JournalDateFilter initialDate={selectedWorkDate} />
            <JournalDeduplicateButton
              duplicateCount={duplicateCount}
              workDate={selectedWorkDate}
            />
            <JournalBulkDeleteControls
              totalEntries={journalEntries.length}
              workDate={selectedWorkDate}
            />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge task">Записей</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {isJournalUnavailable ? "—" : journalEntries.length}
            </div>
            <div className="page-sub">
              {isJournalUnavailable ? "Не удалось загрузить журнал" : "За выбранную дату"}
            </div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge acl">Дата</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {formatDateLabel(selectedWorkDate)}
            </div>
            <div className="page-sub">Рабочий день</div>
          </div>
        </div>

        <div className="section-label">
          {isJournalUnavailable ? "Журнал недоступен" : `Записей: ${journalEntries.length}`}
        </div>
        <JournalEntrySelectionList
          entries={journalEntries}
          isJournalUnavailable={isJournalUnavailable}
        />
      </main>
    </div>
  );
}

function calculateDuplicateCount(journalEntries: JournalEntry[]): number {
  const ticketCounts = new Map<string, number>();

  for (const journalEntry of journalEntries) {
    const normalizedTicketNumber = (journalEntry.ticket_number ?? "").trim();
    if (!normalizedTicketNumber) {
      continue;
    }

    const currentCount = ticketCounts.get(normalizedTicketNumber) ?? 0;
    ticketCounts.set(normalizedTicketNumber, currentCount + 1);
  }

  let duplicateCount = 0;
  for (const ticketCount of ticketCounts.values()) {
    if (ticketCount > 1) {
      duplicateCount += ticketCount - 1;
    }
  }

  return duplicateCount;
}
