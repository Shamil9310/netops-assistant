"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { JournalBulkImportForm } from "@/components/journal-bulk-import-form";
import { extractErrorMessage } from "@/lib/api-error";

type Props = {
  initialWorkDate: string;
};

export function JournalCreateForm({ initialWorkDate }: Props) {
  const router = useRouter();
  const [workDate, setWorkDate] = useState(initialWorkDate);
  const [ticketNumber, setTicketNumber] = useState("");
  const [service, setService] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isImportOpen, setIsImportOpen] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch("/api/journal/entries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          work_date: workDate,
          activity_type: "task",
          status: "open",
          title: ticketNumber.trim() || `Журнал ${workDate}`,
          description: null,
          resolution: null,
          contact: null,
          service: service.trim() || null,
          ticket_number: ticketNumber || null,
          task_url: null,
          started_at: null,
          ended_at: null,
          ended_date: null,
        }),
      });
      const responsePayload = (await response.json()) as unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось создать запись"));
        return;
      }

      setTicketNumber("");
      setService("");
      router.push(`/journal?work_date=${workDate}`);
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="filter-group" style={{ marginBottom: 0 }}>
      <div className="filter-group-title">Новая запись</div>
      <input type="date" className="filter-date-input" value={workDate} onChange={(event) => setWorkDate(event.target.value)} />
      <input
        className="filter-date-input"
        placeholder="SR / номер заявки"
        value={ticketNumber}
        onChange={(event) => setTicketNumber(event.target.value)}
      />
      <input
        className="filter-date-input"
        placeholder="Услуга"
        value={service}
        onChange={(event) => setService(event.target.value)}
      />

      <div className="focus-note">
        <div className="focus-note-label">Подсказка</div>
        <p>В журнале достаточно даты, номера заявки и услуги. Остальное не нужно для выгрузки.</p>
      </div>

      <div className="filter-divider" />
      <button type="button" className="btn btn-ghost" onClick={() => setIsImportOpen((current) => !current)}>
        {isImportOpen ? "Скрыть импорт" : "Массовый импорт"}
      </button>

      {isImportOpen && <JournalBulkImportForm initialWorkDate={workDate} />}

      {error && <div className="form-error">{error}</div>}
      <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
        {isSubmitting ? "Сохранение..." : "+ Запись"}
      </button>
    </form>
  );
}
