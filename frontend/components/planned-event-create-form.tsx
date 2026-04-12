"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { CollapsiblePanel } from "@/components/collapsible-panel";
import { extractErrorMessage } from "@/lib/api-error";
import {
  plannedEventCreateSchema,
  type PlannedEventCreateFormData,
} from "@/lib/schemas";
import { useLocalStorageDraft } from "@/lib/hooks/use-local-storage-draft";

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
  const { draft, setDraft, clearDraft } = useLocalStorageDraft<PlannedEventCreateFormData>(
    "planned-event-create-draft",
    {
      event_type: "meeting",
      title: "",
      description: "",
      external_ref: "",
      scheduled_at: createDefaultScheduledAt(initialWorkDate),
    },
  );
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setDraft((currentDraft) => ({
      ...currentDraft,
      scheduled_at: currentDraft.scheduled_at || createDefaultScheduledAt(initialWorkDate),
    }));
  }, [initialWorkDate, setDraft]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    const validationResult = plannedEventCreateSchema.safeParse(draft);
    if (!validationResult.success) {
      setError(validationResult.error.issues[0]?.message ?? "Проверь заполнение формы");
      setIsSubmitting(false);
      return;
    }
    try {
      const response = await fetch("/api/planned-events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: draft.event_type,
          title: draft.title,
          description: draft.description?.trim() || null,
          external_ref: draft.external_ref?.trim() || null,
          scheduled_at: new Date(draft.scheduled_at).toISOString(),
        }),
      });
      const responsePayload = (await response.json()) as unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось создать событие"));
        return;
      }
      clearDraft();
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <CollapsiblePanel title="Плановое событие" subtitle="События дня скрыты по умолчанию, чтобы панель была компактной.">
      <form onSubmit={onSubmit} className="filter-group" style={{ marginBottom: 0 }}>
        <select
          className="filter-date-input"
          value={draft.event_type}
          onChange={(event) =>
            setDraft((currentDraft) => ({
              ...currentDraft,
              event_type: event.target.value as PlannedEventCreateFormData["event_type"],
            }))
          }
        >
          <option value="meeting">Встреча</option>
          <option value="task">Задача</option>
          <option value="night_work_prep">Подготовка к ночным работам</option>
        </select>
        <div className="focus-note" style={{ marginBottom: 8 }}>
          <div className="focus-note-label">Тип события</div>
          <p>{getEventTypeLabel(draft.event_type)}</p>
        </div>
        <input
          className="filter-date-input"
          placeholder="Заголовок"
          value={draft.title}
          onChange={(event) =>
            setDraft((currentDraft) => ({
              ...currentDraft,
              title: event.target.value,
            }))
          }
          required
        />
        <input
          className="filter-date-input"
          placeholder="SR / External ref"
          value={draft.external_ref ?? ""}
          onChange={(event) =>
            setDraft((currentDraft) => ({
              ...currentDraft,
              external_ref: event.target.value,
            }))
          }
        />
        <input
          type="datetime-local"
          className="filter-date-input"
          value={draft.scheduled_at}
          onChange={(event) =>
            setDraft((currentDraft) => ({
              ...currentDraft,
              scheduled_at: event.target.value,
            }))
          }
          required
        />
        <textarea
          className="filter-date-input"
          placeholder="Описание"
          value={draft.description ?? ""}
          onChange={(event) =>
            setDraft((currentDraft) => ({
              ...currentDraft,
              description: event.target.value,
            }))
          }
        />
        {error && <div className="form-error">{error}</div>}
        <div className="page-sub" style={{ marginTop: -2 }}>
          Черновик сохраняется автоматически
        </div>
        <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
          {isSubmitting ? "Сохранение..." : "Создать"}
        </button>
      </form>
    </CollapsiblePanel>
  );
}
