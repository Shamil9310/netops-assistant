"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import type { JournalActivityStatus, JournalActivityType } from "@/lib/api";

const ACTIVITY_LABELS: Record<JournalActivityType, string> = {
  task: "Задача",
  ticket: "Заявка",
  call: "Звонок",
  meeting: "Встреча",
  escalation: "Эскалация",
  other: "Прочее",
};

function generateTitle(activityType: JournalActivityType, ticketNumber: string, workDate: string): string {
  if (ticketNumber.trim()) {
    return ticketNumber.trim();
  }
  return `${ACTIVITY_LABELS[activityType]} ${workDate}`;
}

function toTimeInputValue(value: string | null | undefined): string {
  if (!value) {
    return "";
  }
  return value.slice(0, 5);
}

type Props = {
  initialWorkDate: string;
  lastEndedAt?: string | null;
};

export function JournalCreateForm({ initialWorkDate, lastEndedAt }: Props) {
  const router = useRouter();
  const [workDate, setWorkDate] = useState(initialWorkDate);
  const [activityType, setActivityType] = useState<JournalActivityType>("task");
  const [status, setStatus] = useState<JournalActivityStatus>("open");
  const [description, setDescription] = useState("");
  const [resolution, setResolution] = useState("");
  const [contact, setContact] = useState("");
  const [ticketNumber, setTicketNumber] = useState("");
  const [taskUrl, setTaskUrl] = useState("");
  const [startedAt, setStartedAt] = useState(toTimeInputValue(lastEndedAt));
  const [endedAt, setEndedAt] = useState("");
  const [endedDate, setEndedDate] = useState(initialWorkDate);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasCrossMidnightRange = Boolean(
    startedAt && endedAt && endedDate === workDate && endedAt < startedAt,
  );

  useEffect(() => {
    if (!startedAt && lastEndedAt) {
      setStartedAt(toTimeInputValue(lastEndedAt));
    }
  }, [lastEndedAt, startedAt]);

  useEffect(() => {
    setEndedDate((current) => (current < workDate ? workDate : current));
  }, [workDate]);

  useEffect(() => {
    let isCancelled = false;

    async function fillStartedAtFromLatestEntry() {
      if (startedAt) {
        return;
      }

      try {
        // Подхватываем время окончания последней записи за день,
        // чтобы следующую запись было быстрее заполнять последовательно.
        const response = await fetch(`/api/journal/entries?work_date=${workDate}`, { method: "GET" });
        if (!response.ok) {
          return;
        }

        const journalEntriesResponse =
          (await response.json()) as { items?: Array<{ ended_at: string | null }> };
        const latestEndedAtValue =
          [...(journalEntriesResponse.items ?? [])]
            .reverse()
            .find((entry) => entry.ended_at)?.ended_at;
        if (!isCancelled && latestEndedAtValue) {
          setStartedAt(toTimeInputValue(latestEndedAtValue));
        }
      } catch {
        // no-op: if entries cannot be loaded, user can still enter time manually
      }
    }

    fillStartedAtFromLatestEntry();
    return () => {
      isCancelled = true;
    };
  }, [workDate, startedAt]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    if (endedDate < workDate) {
      setError("Дата окончания не может быть раньше рабочей даты");
      setIsSubmitting(false);
      return;
    }

    // Для одной и той же даты запрещаем обратный интервал.
    // Если задача завершилась на следующий день, это нужно указать явно через endedDate.
    if (hasCrossMidnightRange) {
      setError("Время окончания не может быть раньше времени начала");
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await fetch("/api/journal/entries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          work_date: workDate,
          activity_type: activityType,
          status,
          title: generateTitle(activityType, ticketNumber, workDate),
          description: description || null,
          resolution: resolution || null,
          contact: contact || null,
          ticket_number: ticketNumber || null,
          task_url: taskUrl || null,
          started_at: startedAt || null,
          ended_at: endedAt || null,
          ended_date: endedAt ? endedDate : null,
        }),
      });
      const responsePayload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        setError(responsePayload.detail ?? "Не удалось создать запись");
        return;
      }

      setDescription("");
      setResolution("");
      setContact("");
      setTicketNumber("");
      setTaskUrl("");
      setStartedAt(endedAt || startedAt);
      setEndedAt("");
      setEndedDate(workDate);
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

      <input className="filter-date-input" placeholder="SR / номер заявки" value={ticketNumber} onChange={(event) => setTicketNumber(event.target.value)} />
      <input className="filter-date-input" placeholder="Контакт (от кого пришло)" value={contact} onChange={(event) => setContact(event.target.value)} />
      <input className="filter-date-input" placeholder="Ссылка на задачу (BPM и т.п.)" value={taskUrl} onChange={(event) => setTaskUrl(event.target.value)} />
      <input type="time" className="filter-date-input" value={startedAt} onChange={(event) => setStartedAt(event.target.value)} />
      <input type="time" className="filter-date-input" value={endedAt} onChange={(event) => setEndedAt(event.target.value)} />
      <input type="date" className="filter-date-input" value={endedDate} onChange={(event) => setEndedDate(event.target.value)} />
      {hasCrossMidnightRange && (
        <div className="focus-note" style={{ marginBottom: 20, marginTop: -8 }}>
          <div className="focus-note-label">Предупреждение</div>
          <p>
            Для той же даты время окончания не может быть раньше времени начала.
            Если задача закрыта на следующий день, укажи дату окончания ниже.
          </p>
        </div>
      )}
      <textarea className="filter-date-input" placeholder="Описание" value={description} onChange={(event) => setDescription(event.target.value)} />
      <textarea className="filter-date-input" placeholder="Решение" value={resolution} onChange={(event) => setResolution(event.target.value)} />

      {error && <div className="form-error">{error}</div>}
      <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
        {isSubmitting ? "Сохранение..." : "+ Запись"}
      </button>
    </form>
  );
}
