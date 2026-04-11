"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { extractErrorMessage } from "@/lib/api-error";

type ReportType = "daily" | "weekly" | "range";
type ReportProfile = "engineer" | "manager";
type ServiceFilterMode = "all" | "include" | "exclude" | "empty";

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
  const [reportType, setReportType] = useState<ReportType>("range");
  const [reportDate, setReportDate] = useState(formatDateForInput(today));
  const [weekStart, setWeekStart] = useState(formatDateForInput(getWeekMonday(today)));
  const [dateFrom, setDateFrom] = useState(formatDateForInput(today));
  const [dateTo, setDateTo] = useState(formatDateForInput(today));
  const [formatProfile, setFormatProfile] = useState<ReportProfile>("engineer");
  const [serviceFilterMode, setServiceFilterMode] =
    useState<ServiceFilterMode>("all");
  const [serviceFilterValue, setServiceFilterValue] = useState("");
  const [selectedServices, setSelectedServices] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const isInvalidRange = reportType === "range" && dateFrom > dateTo;
  const serviceOptions = useMemo(
    () =>
      Array.from(
        new Set(
          serviceFilterValue
            .split("\n")
            .map((service) => service.trim())
            .filter(Boolean),
        ),
      ).sort((leftService, rightService) =>
        leftService.localeCompare(rightService, "ru"),
      ),
    [serviceFilterValue],
  );

  function toggleServiceSelection(service: string) {
    setSelectedServices((currentServices) => {
      if (currentServices.includes(service)) {
        return currentServices.filter(
          (currentService) => currentService !== service,
        );
      }
      return [...currentServices, service];
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    if (reportType === "range" && dateFrom > dateTo) {
      setError("Дата начала не может быть позже даты окончания");
      setIsLoading(false);
      return;
    }

    const reportRequestBody =
      reportType === "daily"
        ? {
            report_type: "daily",
            report_date: reportDate,
            format_profile: formatProfile,
            service_filter_mode: serviceFilterMode,
            service_filters: selectedServices,
          }
        : reportType === "weekly"
          ? {
              report_type: "weekly",
              week_start: weekStart,
              format_profile: formatProfile,
              service_filter_mode: serviceFilterMode,
              service_filters: selectedServices,
            }
          : {
              report_type: "range",
              date_from: dateFrom,
              date_to: dateTo,
              format_profile: formatProfile,
              service_filter_mode: serviceFilterMode,
              service_filters: selectedServices,
            };

    try {
      const response = await fetch("/api/reports/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reportRequestBody),
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
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <div className="filter-date-label">Сформировать отчёт</div>
      <select
        value={reportType}
        onChange={(event) => setReportType(event.target.value as ReportType)}
        className="filter-date-input"
      >
        <option value="range">От и до</option>
        <option value="daily">Дневной</option>
        <option value="weekly">Недельный</option>
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
          {isInvalidRange && <div className="form-error">Дата начала не может быть позже даты окончания</div>}
        </>
      )}

      <div className="focus-note" style={{ marginTop: 4 }}>
        <div className="focus-note-label">Фильтр услуг</div>
        <select
          value={serviceFilterMode}
          onChange={(event) =>
            setServiceFilterMode(event.target.value as ServiceFilterMode)
          }
          className="filter-date-input"
        >
          <option value="all">Все услуги</option>
          <option value="include">Только выбранные услуги</option>
          <option value="exclude">Исключить выбранные услуги</option>
          <option value="empty">Только без услуги</option>
        </select>
        <textarea
          className="filter-date-input"
          value={serviceFilterValue}
          onChange={(event) => setServiceFilterValue(event.target.value)}
          disabled={serviceFilterMode === "all" || serviceFilterMode === "empty"}
          placeholder="Вставь список услуг, по одной на строку"
          style={{ minHeight: 96, resize: "vertical" }}
        />
        {serviceOptions.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div className="plan-sub" style={{ marginTop: 0 }}>
              Можно отметить любое количество услуг.
            </div>
            <div style={{ display: "grid", gap: 6, maxHeight: 180, overflow: "auto" }}>
              {serviceOptions.map((service) => (
                <label
                  key={service}
                  className="journal-entry-selector-row"
                >
                  <input
                    className="journal-entry-selector"
                    type="checkbox"
                    checked={selectedServices.includes(service)}
                    onChange={() => toggleServiceSelection(service)}
                    disabled={
                      serviceFilterMode === "all" || serviceFilterMode === "empty"
                    }
                  />
                  <span>{service}</span>
                </label>
              ))}
            </div>
          </div>
        )}
      </div>

      {error && <div className="form-error">{error}</div>}

      <button type="submit" className="btn btn-primary" disabled={isLoading}>
        {isLoading ? "Генерация..." : "Сформировать"}
      </button>
    </form>
  );
}
