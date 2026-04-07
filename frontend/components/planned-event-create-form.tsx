"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type Props = {
  initialWorkDate: string;
};

export function PlannedEventCreateForm({ initialWorkDate }: Props) {
  const router = useRouter();
  const [eventType, setEventType] = useState("meeting");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [externalRef, setExternalRef] = useState("");
  const [scheduledAt, setScheduledAt] = useState(`${initialWorkDate}T10:00`);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await fetch("/api/planned-events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: eventType,
          title,
          description: description || null,
          external_ref: externalRef || null,
          scheduled_at: new Date(scheduledAt).toISOString(),
        }),
      });
      const body = (await response.json()) as { detail?: string };
      if (!response.ok) {
        setError(body.detail ?? "Не удалось создать событие");
        return;
      }
      setTitle("");
      setDescription("");
      setExternalRef("");
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="filter-group" style={{ marginBottom: 0 }}>
      <div className="filter-group-title">Плановое событие</div>
      <select className="filter-date-input" value={eventType} onChange={(event) => setEventType(event.target.value)}>
        <option value="call">Звонок</option>
        <option value="meeting">Встреча</option>
        <option value="task">Задача</option>
        <option value="maintenance">Обслуживание</option>
        <option value="change">Изменение</option>
        <option value="other">Прочее</option>
      </select>
      <input className="filter-date-input" placeholder="Заголовок" value={title} onChange={(event) => setTitle(event.target.value)} required />
      <input className="filter-date-input" placeholder="SR / External ref" value={externalRef} onChange={(event) => setExternalRef(event.target.value)} />
      <input type="datetime-local" className="filter-date-input" value={scheduledAt} onChange={(event) => setScheduledAt(event.target.value)} required />
      <textarea className="filter-date-input" placeholder="Описание" value={description} onChange={(event) => setDescription(event.target.value)} />
      {error && <div className="form-error">{error}</div>}
      <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
        {isSubmitting ? "Сохранение..." : "Создать"}
      </button>
    </form>
  );
}
