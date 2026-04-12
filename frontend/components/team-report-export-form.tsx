"use client";

import { useMemo, useState } from "react";

import { CollapsiblePanel } from "@/components/collapsible-panel";
import type { TeamMember } from "@/lib/api";

type TeamReportType = "daily" | "weekly" | "range";

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

export function TeamReportExportForm({ users }: { users: TeamMember[] }) {
  const today = useMemo(() => new Date(), []);
  const [reportType, setReportType] = useState<TeamReportType>("weekly");
  const [selectedUserId, setSelectedUserId] = useState(users[0]?.id ?? "");
  const [reportDate, setReportDate] = useState(formatDateForInput(today));
  const [weekStart, setWeekStart] = useState(formatDateForInput(getWeekMonday(today)));
  const [dateFrom, setDateFrom] = useState(formatDateForInput(today));
  const [dateTo, setDateTo] = useState(formatDateForInput(today));

  if (users.length === 0) {
    return (
      <div className="focus-note">
        <div className="focus-note-label">Нет сотрудников</div>
        <p>Список пользователей недоступен для выгрузки отчётов.</p>
      </div>
    );
  }

  return (
    <CollapsiblePanel title="Выгрузка отчётов сотрудников" subtitle="Панель компактная и открывается только когда нужна.">
      <form method="get" action="/api/team/reports/export" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <select
          className="filter-date-input"
          name="user_id"
          value={selectedUserId}
          onChange={(event) => setSelectedUserId(event.target.value)}
        >
          {users.map((member) => (
            <option key={member.id} value={member.id}>
              {member.full_name} ({member.username})
            </option>
          ))}
        </select>

        <select
          className="filter-date-input"
          name="report_type"
          value={reportType}
          onChange={(event) => setReportType(event.target.value as TeamReportType)}
        >
          <option value="daily">Дневной</option>
          <option value="weekly">Недельный</option>
          <option value="range">За период</option>
        </select>

        {reportType === "daily" && (
          <input
            type="date"
            className="filter-date-input"
            name="report_date"
            value={reportDate}
            onChange={(event) => setReportDate(event.target.value)}
            required
          />
        )}

        {reportType === "weekly" && (
          <input
            type="date"
            className="filter-date-input"
            name="week_start"
            value={weekStart}
            onChange={(event) => setWeekStart(event.target.value)}
            required
          />
        )}

        {reportType === "range" && (
          <>
            <input
              type="date"
              className="filter-date-input"
              name="date_from"
              value={dateFrom}
              onChange={(event) => setDateFrom(event.target.value)}
              required
            />
            <input
              type="date"
              className="filter-date-input"
              name="date_to"
              value={dateTo}
              onChange={(event) => setDateTo(event.target.value)}
              required
            />
          </>
        )}

        <button type="submit" className="btn btn-primary">
          Выгрузить MD
        </button>
      </form>
    </CollapsiblePanel>
  );
}
