"use client";

import { useState } from "react";

import { extractErrorMessage } from "@/lib/api-error";

type Props = {
  totalEntries: number;
  workDate: string;
};

type BulkDeleteResponse = {
  scope: "work_date" | "all";
  removed: number;
  work_date: string | null;
};

export function JournalBulkDeleteControls({ totalEntries, workDate }: Props) {
  const [isDeletingForDate, setIsDeletingForDate] = useState(false);
  const [isDeletingAll, setIsDeletingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function deleteForDate() {
    if (totalEntries === 0) {
      return;
    }

    const userConfirmed = window.confirm(
      "Удалить все записи за выбранную дату? Это действие нельзя отменить."
    );
    if (!userConfirmed) {
      return;
    }

    setIsDeletingForDate(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`/api/journal/entries/delete-for-date?work_date=${workDate}`, {
        method: "POST",
      });
      const responsePayload = (await response.json()) as BulkDeleteResponse | unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось удалить записи за дату"));
        return;
      }

      const deleteResult = responsePayload as BulkDeleteResponse;
      setSuccess(`Удалено записей за дату: ${deleteResult.removed}`);
      window.location.reload();
    } catch {
      setError("Ошибка массового удаления за дату");
    } finally {
      setIsDeletingForDate(false);
    }
  }

  async function deleteAll() {
    const userConfirmed = window.confirm(
      "Удалить вообще все записи журнала? Это действие нельзя отменить."
    );
    if (!userConfirmed) {
      return;
    }

    const secondConfirmation = window.confirm(
      "Подтверди ещё раз: будут удалены все записи журнала текущего пользователя."
    );
    if (!secondConfirmation) {
      return;
    }

    setIsDeletingAll(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/journal/entries/delete-all", {
        method: "POST",
      });
      const responsePayload = (await response.json()) as BulkDeleteResponse | unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось удалить все записи журнала"));
        return;
      }

      const deleteResult = responsePayload as BulkDeleteResponse;
      setSuccess(`Удалено всех записей: ${deleteResult.removed}`);
      window.location.href = `/journal?work_date=${workDate}`;
    } catch {
      setError("Ошибка полной очистки журнала");
    } finally {
      setIsDeletingAll(false);
    }
  }

  // Два действия разделены явно, чтобы пользователь не перепутал
  // очистку текущего дня с полной очисткой всего личного журнала.
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button
          type="button"
          className="btn btn-sm"
          onClick={deleteForDate}
          disabled={isDeletingForDate || isDeletingAll || totalEntries === 0}
          title={
            totalEntries === 0
              ? "За выбранную дату нет записей для удаления"
              : "Удалить все записи только за текущую рабочую дату"
          }
        >
          {isDeletingForDate ? "Очистка..." : "Очистить дату"}
        </button>
        <button
          type="button"
          className="btn btn-sm btn-danger"
          onClick={deleteAll}
          disabled={isDeletingForDate || isDeletingAll}
          title="Удалить вообще все записи журнала текущего пользователя"
        >
          {isDeletingAll ? "Удаление всего..." : "Удалить всё"}
        </button>
      </div>
      {error && <span className="form-error">{error}</span>}
      {success && <span className="form-success">{success}</span>}
    </div>
  );
}
