"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { extractErrorMessage } from "@/lib/api-error";

type Props = {
  entryId: string;
  title: string;
  ticketNumber: string | null;
  service: string | null;
  workDate: string;
  backHref: string;
};

export function JournalEntryDetail({
  entryId,
  title,
  ticketNumber,
  service,
  workDate,
  backHref,
}: Props) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onDelete() {
    if (!window.confirm("Удалить запись?")) {
      return;
    }

    setError(null);
    setIsLoading(true);
    try {
      const response = await fetch(`/api/journal/entries/${entryId}`, { method: "DELETE" });
      if (!response.ok) {
        const responsePayload = (await response.json()) as unknown;
        setError(extractErrorMessage(responsePayload, "Ошибка удаления"));
        return;
      }
      window.location.href = backHref;
    } catch {
      setError("Ошибка удаления");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="report-block journal-entry-page">
      <div className="modal-header journal-entry-header">
        <div>
          <div className="modal-sr">{title}</div>
          <div className="modal-meta">Дата: {workDate}</div>
        </div>
        <Link className="modal-close" href={backHref} aria-label="Назад">
          ×
        </Link>
      </div>

      <div className="modal-body journal-entry-body">
        <div className="focus-note">
          <div className="focus-note-label">Номер</div>
          <p>{ticketNumber ?? "Не заполнено"}</p>
        </div>
        <div className="focus-note">
          <div className="focus-note-label">Услуга</div>
          <p>{service ?? "Не заполнено"}</p>
        </div>
        {error && <div className="form-error">{error}</div>}
      </div>

      <div className="modal-footer">
        <button type="button" className="btn btn-sm btn-danger" onClick={onDelete} disabled={isLoading}>
          Удалить
        </button>
        <button type="button" className="btn btn-sm" onClick={() => router.push(backHref)}>
          Закрыть
        </button>
      </div>
    </div>
  );
}
