"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { extractErrorMessage } from "@/lib/api-error";

type Props = {
  initialWorkDate: string;
};

function getLocalIsoDate(): string {
  return new Date().toLocaleDateString("en-CA");
}

function getLocalTimeInputValue(date: Date): string {
  return date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function createDefaultScheduledAt(initialWorkDate: string): string {
  const now = new Date();
  if (initialWorkDate === getLocalIsoDate()) {
    return `${initialWorkDate}T${getLocalTimeInputValue(now)}`;
  }
  return `${initialWorkDate}T10:00`;
}

function getEventTypeLabel(value: string): string {
  const labels: Record<string, string> = {
    meeting: "Встреча",
    task: "Задача",
    night_work_prep: "Подготовка к ночным работам",
  };
  return labels[value] ?? value;
}

export function PlannedEventCreateForm({ initialWorkDate }: Props) {
  const router = useRouter();
  const [eventType, setEventType] = useState("meeting");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [externalRef, setExternalRef] = useState("");
  const [scheduledAt, setScheduledAt] = useState(() =>
    createDefaultScheduledAt(initialWorkDate),
  );
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setScheduledAt(createDefaultScheduledAt(initialWorkDate));
  }, [initialWorkDate]);

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
      const responsePayload = (await response.json()) as unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось создать событие"));
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
        <option value="meeting">Встреча</option>
        <option value="task">Задача</option>
        <option value="night_work_prep">Подготовка к ночным работам</option>
      </select>
      <div className="focus-note" style={{ marginBottom: 8 }}>
        <div className="focus-note-label">Тип события</div>
        <p>{getEventTypeLabel(eventType)}</p>
      </div>
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
