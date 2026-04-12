"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { extractErrorMessage } from "@/lib/api-error";

function formatDateForInput(dateValue: Date): string {
  return dateValue.toISOString().slice(0, 10);
}

export function ReportGenerateForm() {
  const router = useRouter();
  const today = useMemo(() => new Date(), []);
  const [dateFrom, setDateFrom] = useState(formatDateForInput(today));
  const [dateTo, setDateTo] = useState(formatDateForInput(today));
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const isInvalidRange = dateFrom > dateTo;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    if (dateFrom > dateTo) {
      setError("Дата начала не может быть позже даты окончания");
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/reports/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_type: "range",
          date_from: dateFrom,
          date_to: dateTo,
          format_profile: "engineer",
          service_filter_mode: "all",
          service_filters: [],
        }),
      });
      const responsePayload = (await response.json()) as { report_id?: string } & Record<string, unknown>;
      if (!response.ok || !responsePayload.report_id) {
        setError(extractErrorMessage(responsePayload, "Не удалось сгенерировать отчёт"));
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
    <div className="report-tool">
      <div className="filter-group-title">Сформировать отчёт</div>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <div className="filter-date-label">От</div>
        <input
          type="date"
          className="filter-date-input"
          value={dateFrom}
          onChange={(event) => setDateFrom(event.target.value)}
        />

        <div className="filter-date-label">До</div>
        <input
          type="date"
          className="filter-date-input"
          value={dateTo}
          onChange={(event) => setDateTo(event.target.value)}
        />

        {isInvalidRange && <div className="form-error">Дата начала не может быть позже даты окончания</div>}

        {error && <div className="form-error">{error}</div>}

        <button type="submit" className="btn btn-primary" disabled={isLoading}>
          {isLoading ? "Сборка..." : "Собрать в файл"}
        </button>
      </form>
    </div>
  );
}
