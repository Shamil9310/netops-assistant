import { Sidebar } from "@/components/sidebar";
import { JournalCreateForm } from "@/components/journal-create-form";
import { JournalDateFilter } from "@/components/journal-date-filter";
import { JournalDeduplicateButton } from "@/components/journal-deduplicate-button";
import { JournalBulkDeleteControls } from "@/components/journal-bulk-delete-controls";
import { JournalEntrySelectionList } from "@/components/journal-entry-selection-list";
import { PageHero } from "@/components/page-hero";
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

      <main className="content-col">
        <PageHero
          eyebrow="Оперативный журнал"
          title="Журнал"
          subtitle={`Записи за рабочую дату ${formatDateLabel(selectedWorkDate)}. Здесь создаём и очищаем рабочую историю.`}
          actions={
            <>
              <JournalDateFilter initialDate={selectedWorkDate} />
              <JournalDeduplicateButton duplicateCount={duplicateCount} workDate={selectedWorkDate} />
              <JournalBulkDeleteControls totalEntries={journalEntries.length} workDate={selectedWorkDate} />
            </>
          }
          stats={[
            { label: "Записей", value: isJournalUnavailable ? "—" : String(journalEntries.length), hint: "За выбранную дату" },
            { label: "Дубликаты", value: isJournalUnavailable ? "—" : String(duplicateCount), hint: "Нужно убрать" },
            { label: "Дата", value: formatDateLabel(selectedWorkDate), hint: "Рабочий день" },
          ]}
        />

        <div className="focus-note" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div>
            <div className="focus-note-label">Сводка</div>
            <p style={{ margin: 0 }}>
              {isJournalUnavailable
                ? "Не удалось загрузить журнал"
                : `За выбранную дату доступно ${journalEntries.length} записей, дубликатов ${duplicateCount}.`}
            </p>
          </div>
          <div className="page-sub" style={{ whiteSpace: "nowrap" }}>
            {formatDateLabel(selectedWorkDate)}
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

      <aside className="filter-col">
        <div className="filter-col-title">Журнал</div>
        <JournalCreateForm key={selectedWorkDate} initialWorkDate={selectedWorkDate} />
      </aside>
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
