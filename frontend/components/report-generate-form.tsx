"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

type ReportType = "daily" | "weekly" | "range";
type ReportProfile = "engineer" | "manager";

function formatDateForInput(dateValue: Date): string {
  return dateValue.toISOString().slice(0, 10);
}

function getWeekMonday(dateValue: Date): Date {
  const mondayDate = new Date(dateValue);
  const dayOfWeek = mondayDate.getUTCDay();
  const dayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  mondayDate.setUTCDate(mondayDate.getUTCDate() + dayOffset);
  return mondayDate;
}

export function ReportGenerateForm() {
  const router = useRouter();
  const today = useMemo(() => new Date(), []);
  const [reportType, setReportType] = useState<ReportType>("daily");
  const [reportDate, setReportDate] = useState(formatDateForInput(today));
  const [weekStart, setWeekStart] = useState(formatDateForInput(getWeekMonday(today)));
  const [dateFrom, setDateFrom] = useState(formatDateForInput(today));
  const [dateTo, setDateTo] = useState(formatDateForInput(today));
  const [formatProfile, setFormatProfile] = useState<ReportProfile>("engineer");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    const reportRequestBody =
      reportType === "daily"
        ? { report_type: "daily", report_date: reportDate, format_profile: formatProfile }
        : reportType === "weekly"
          ? { report_type: "weekly", week_start: weekStart, format_profile: formatProfile }
          : { report_type: "range", date_from: dateFrom, date_to: dateTo, format_profile: formatProfile };

    try {
      const response = await fetch("/api/reports/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reportRequestBody),
      });
      const responsePayload = (await response.json()) as { report_id?: string; detail?: string };
      if (!response.ok || !responsePayload.report_id) {
        setError(responsePayload.detail ?? "Не удалось сгенерировать отчёт");
        return;
      }

      router.push(`/reports?report_id=${responsePayload.report_id}`);
      router.refresh();
    } catch {
      setError("Ошибка соединения с приложением");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div className="filter-date-label">Сформировать отчёт</div>
      <select
        value={reportType}
        onChange={(event) => setReportType(event.target.value as ReportType)}
        className="filter-date-input"
      >
        <option value="daily">Дневной</option>
        <option value="weekly">Недельный</option>
        <option value="range">За период</option>
      </select>

      <select
        value={formatProfile}
        onChange={(event) => setFormatProfile(event.target.value as ReportProfile)}
        className="filter-date-input"
      >
        <option value="engineer">Профиль: инженерный</option>
        <option value="manager">Профиль: руководительский</option>
      </select>

      {reportType === "daily" && (
        <input
          type="date"
          className="filter-date-input"
          value={reportDate}
          onChange={(event) => setReportDate(event.target.value)}
        />
      )}

      {reportType === "weekly" && (
        <input
          type="date"
          className="filter-date-input"
          value={weekStart}
          onChange={(event) => setWeekStart(event.target.value)}
        />
      )}

      {reportType === "range" && (
        <>
          <input
            type="date"
            className="filter-date-input"
            value={dateFrom}
            onChange={(event) => setDateFrom(event.target.value)}
          />
          <input
            type="date"
            className="filter-date-input"
            value={dateTo}
            onChange={(event) => setDateTo(event.target.value)}
          />
        </>
      )}

      {error && <div className="form-error">{error}</div>}

      <button type="submit" className="btn btn-primary" disabled={isLoading}>
        {isLoading ? "Генерация..." : "Сформировать"}
      </button>
    </form>
  );
}
