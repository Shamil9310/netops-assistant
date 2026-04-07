import { Sidebar } from "@/components/sidebar";
import { ReportFinalizeButton } from "@/components/report-finalize-button";
import { ReportGenerateForm } from "@/components/report-generate-form";
import { ReportRegenerateDraftButton } from "@/components/report-regenerate-draft-button";
import { ReportRefreshButton } from "@/components/report-refresh-button";
import { getReportHistory, getReportPreview } from "@/lib/api";
import { requireUser } from "@/lib/auth";

type SearchParams = Record<string, string | string[] | undefined>;

function toSingleValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

function formatDate(value: string): string {
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

function mapReportType(type: string): string {
  const labels: Record<string, string> = {
    daily: "День",
    weekly: "Неделя",
    range: "Период",
    night_work_result: "Ночные работы",
  };
  return labels[type] ?? type;
}

export default async function ReportsPage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const history = await getReportHistory();
  const reportIdFromUrl = toSingleValue(searchParams?.report_id);
  const selectedReportId = reportIdFromUrl || history?.[0]?.id || "";
  const preview = selectedReportId ? await getReportPreview(selectedReportId) : null;
  const publicApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  return (
    <div className="shell">
      <Sidebar user={user} />

      {/* Filter col */}
      <aside className="filter-col">
        <div className="filter-col-title">Параметры</div>

        <div className="filter-group" style={{ marginBottom: 20 }}>
          <ReportGenerateForm />
        </div>

        <div className="filter-divider" />

        <div className="filter-group" style={{ marginBottom: 20 }}>
          <div className="filter-group-title">История генераций</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {(history ?? []).slice(0, 20).map((record) => (
              <a
                key={record.id}
                href={`/reports?report_id=${record.id}`}
                className={record.id === selectedReportId ? "filter-chip active" : "filter-chip"}
                style={{ textAlign: "left" }}
              >
                <span className="chip-dot" style={{ background: "var(--blue)" }} />
                {mapReportType(record.report_type)}
                <span className="chip-count">{record.period_from}</span>
              </a>
            ))}
            {(history ?? []).length === 0 && (
              <div className="focus-note">
                <div className="focus-note-label">Нет данных</div>
                <p>Сначала сгенерируй отчёт через backend API.</p>
              </div>
            )}
          </div>
        </div>

        <div className="focus-note">
          <div className="focus-note-label">Примечание</div>
          <p>UI работает с уже сгенерированными отчётами: предпросмотр, история и экспорт.</p>
        </div>
      </aside>

      {/* Content */}
      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Отчёты</div>
            <div className="page-sub">Предпросмотр, история и экспорт сгенерированных отчётов</div>
          </div>
        </div>

        <div className="section-label">
          {preview ? `${mapReportType(preview.report_type)} · ${preview.period_from} — ${preview.period_to}` : "Отчёт не выбран"}
        </div>

        <div className="report-block">
          {preview ? (
            <>
              <div className="report-header">
                <div>
                  <div className="report-header-title">
                    {mapReportType(preview.report_type)} · {preview.period_from} — {preview.period_to}
                  </div>
                  <div className="report-header-sub">Сформирован: {formatDate(preview.generated_at)} · {user.full_name}</div>
                  <div className="report-header-sub">Статус: {preview.report_status}</div>
                  {preview.report_status === "final" && preview.updates_after_finalization > 0 && (
                    <div className="report-header-sub">
                      После фиксации добавлено новых записей: {preview.updates_after_finalization}
                    </div>
                  )}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  {preview.report_status === "draft" && <ReportRefreshButton reportId={preview.report_id} />}
                  {preview.report_status === "draft" && <ReportFinalizeButton reportId={preview.report_id} />}
                  {preview.report_status === "final" && preview.updates_after_finalization > 0 && (
                    <ReportRegenerateDraftButton reportId={preview.report_id} />
                  )}
                </div>
              </div>
              <pre className="export">{preview.content_md}</pre>
              <div className="export-bar">
                <span className="export-label">Скачать:</span>
                <a className="export-btn" href={`${publicApiBaseUrl}/api/v1/reports/${preview.report_id}/export/txt`}>📄 TXT</a>
                <a className="export-btn" href={`${publicApiBaseUrl}/api/v1/reports/${preview.report_id}/export/md`}>📝 MD</a>
                <a className="export-btn" href={`${publicApiBaseUrl}/api/v1/reports/${preview.report_id}/export/docx`}>DOCX</a>
                <a className="export-btn" href={`${publicApiBaseUrl}/api/v1/reports/${preview.report_id}/export/pdf`}>PDF</a>
              </div>
            </>
          ) : (
            <div className="focus-note">
              <div className="focus-note-label">Нет выбранного отчёта</div>
              <p>Сгенерируй отчёт через backend API и открой его из истории.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
