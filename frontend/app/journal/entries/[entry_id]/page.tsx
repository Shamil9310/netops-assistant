import { notFound } from "next/navigation";

import { Sidebar } from "@/components/sidebar";
import { JournalEntryDetail } from "@/components/journal-entry-detail";
import { getJournalEntryById } from "@/lib/api";
import { formatDateLabel } from "@/lib/date-format";
import { requireUser } from "@/lib/auth";

type RouteParams = Promise<{ entry_id: string }>;

export default async function JournalEntryPage({ params }: { params: RouteParams }) {
  const user = await requireUser();
  const { entry_id: entryId } = await params;
  const entry = await getJournalEntryById(entryId);

  if (!entry) {
    notFound();
  }

  return (
    <div className="shell">
      <Sidebar user={user} />

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Запись журнала</div>
            <div className="page-sub">Отдельная страница записи, которую можно открыть в новой вкладке.</div>
          </div>
        </div>

        <JournalEntryDetail
          entryId={entry.id}
          title={entry.title}
          ticketNumber={entry.ticket_number}
          service={entry.service}
          workDate={formatDateLabel(entry.work_date)}
          backHref={`/journal?work_date=${entry.work_date}`}
        />
      </main>
    </div>
  );
}
