"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import type { JournalActivityStatus, JournalActivityType } from "@/lib/api";

type Props = {
  initialWorkDate: string;
};

export function JournalCreateForm({ initialWorkDate }: Props) {
  const router = useRouter();
  const [workDate, setWorkDate] = useState(initialWorkDate);
  const [activityType, setActivityType] = useState<JournalActivityType>("task");
  const [status, setStatus] = useState<JournalActivityStatus>("open");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [ticketNumber, setTicketNumber] = useState("");
  const [startedAt, setStartedAt] = useState("");
  const [endedAt, setEndedAt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
          activity_type: activityType,
          status,
          title,
          description: description || null,
          ticket_number: ticketNumber || null,
          started_at: startedAt || null,
          ended_at: endedAt || null,
        }),
      });
      const body = (await response.json()) as { detail?: string };
      if (!response.ok) {
        setError(body.detail ?? "Не удалось создать запись");
        return;
      }

      setTitle("");
      setDescription("");
      setTicketNumber("");
      setStartedAt("");
      setEndedAt("");
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

      <select className="filter-date-input" value={activityType} onChange={(event) => setActivityType(event.target.value as JournalActivityType)}>
        <option value="task">Задача</option>
        <option value="ticket">Заявка</option>
        <option value="call">Звонок</option>
        <option value="meeting">Встреча</option>
        <option value="escalation">Эскалация</option>
        <option value="other">Прочее</option>
      </select>

      <select className="filter-date-input" value={status} onChange={(event) => setStatus(event.target.value as JournalActivityStatus)}>
        <option value="open">Открыта</option>
        <option value="in_progress">В работе</option>
        <option value="closed">Закрыта</option>
        <option value="cancelled">Отменена</option>
      </select>

      <input className="filter-date-input" placeholder="Заголовок" value={title} onChange={(event) => setTitle(event.target.value)} required />
      <input className="filter-date-input" placeholder="SR / Ticket" value={ticketNumber} onChange={(event) => setTicketNumber(event.target.value)} />
      <input type="time" className="filter-date-input" value={startedAt} onChange={(event) => setStartedAt(event.target.value)} />
      <input type="time" className="filter-date-input" value={endedAt} onChange={(event) => setEndedAt(event.target.value)} />
      <textarea className="filter-date-input" placeholder="Описание" value={description} onChange={(event) => setDescription(event.target.value)} />

      {error && <div className="form-error">{error}</div>}
      <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
        {isSubmitting ? "Сохранение..." : "+ Запись"}
      </button>
    </form>
  );
}
