import { Sidebar } from "@/components/sidebar";
import { ReportGenerateForm } from "@/components/report-generate-form";
import { getReportPreview } from "@/lib/api";
import { formatDateLabel, formatDateTimeLabel } from "@/lib/date-format";
import { requireUser } from "@/lib/auth";

type SearchParams = Record<string, string | string[] | undefined>;

function toSingleValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

export default async function ReportsPage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const reportIdFromUrl = toSingleValue(searchParams?.report_id);
  const selectedReportId = reportIdFromUrl;
  const preview = selectedReportId ? await getReportPreview(selectedReportId) : null;
  const publicApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  return (
    <div className="shell">
      <Sidebar user={user} />

      <main className="content-col">
        <div className="focus-note" style={{ maxWidth: 640 }}>
          <div className="focus-note-label">Отчёты</div>
          <p>Выбери период слева, собери файл и скачай его справа.</p>
        </div>
      </main>

      <aside className="filter-col">
        <div className="filter-col-title">Параметры</div>
        <ReportGenerateForm />
        {preview ? (
          <div className="report-tool">
            <div className="filter-group-title">Готовый файл</div>
            <div className="focus-note">
              <div className="focus-note-label">Собран</div>
              <p>
                {formatDateLabel(preview.period_from)} — {formatDateLabel(preview.period_to)}
              </p>
              <p>Файл готов к скачиванию.</p>
            </div>
            <a className="btn btn-primary" href={`${publicApiBaseUrl}/api/v1/reports/${preview.report_id}/export/md`}>
              Скачать файл
            </a>
          </div>
        ) : (
          <div className="focus-note">
            <div className="focus-note-label">Файл не собран</div>
            <p>Укажи период и нажми кнопку сбора.</p>
          </div>
        )}
      </aside>
    </div>
  );
}
