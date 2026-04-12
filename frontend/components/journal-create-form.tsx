"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { JournalBulkImportForm } from "@/components/journal-bulk-import-form";
import { CollapsiblePanel } from "@/components/collapsible-panel";
import { extractErrorMessage } from "@/lib/api-error";
import {
  journalQuickCreateSchema,
  type JournalQuickCreateFormData,
} from "@/lib/schemas";
import { useLocalStorageDraft } from "@/lib/hooks/use-local-storage-draft";

type Props = {
  initialWorkDate: string;
};

export function JournalCreateForm({ initialWorkDate }: Props) {
  const router = useRouter();
  const { draft, setDraft, clearDraft } = useLocalStorageDraft<JournalQuickCreateFormData>(
    "journal-create-draft",
    {
      work_date: initialWorkDate,
      ticket_number: "",
      service: "",
    },
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isImportOpen, setIsImportOpen] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const validationResult = journalQuickCreateSchema.safeParse({
      work_date: draft.work_date,
      ticket_number: draft.ticket_number ?? "",
      service: draft.service ?? "",
    });
    if (!validationResult.success) {
      setError(validationResult.error.issues[0]?.message ?? "Проверь заполнение формы");
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await fetch("/api/journal/entries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          work_date: draft.work_date,
          activity_type: "task",
          status: "open",
          title: draft.ticket_number?.trim() || `Журнал ${draft.work_date}`,
          description: null,
          resolution: null,
          contact: null,
          service: (draft.service ?? "").trim() || null,
          ticket_number: (draft.ticket_number ?? "").trim() || null,
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

      clearDraft();
      router.push(`/journal?work_date=${draft.work_date}`);
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <CollapsiblePanel
      title="Новая запись"
      subtitle="Дата, номер заявки и услуга. Импорт и доп. поля скрыты по умолчанию."
    >
      <form onSubmit={onSubmit} className="filter-group" style={{ marginBottom: 0 }}>
        <input
          type="date"
          className="filter-date-input"
          value={draft.work_date}
          onChange={(event) =>
            setDraft((currentDraft) => ({
              ...currentDraft,
              work_date: event.target.value,
            }))
          }
        />
        <input
          className="filter-date-input"
          placeholder="SR / номер заявки"
          value={draft.ticket_number ?? ""}
          onChange={(event) =>
            setDraft((currentDraft) => ({
              ...currentDraft,
              ticket_number: event.target.value,
            }))
          }
        />
        <input
          className="filter-date-input"
          placeholder="Услуга"
          value={draft.service ?? ""}
          onChange={(event) =>
            setDraft((currentDraft) => ({
              ...currentDraft,
              service: event.target.value,
            }))
          }
        />

        <div className="focus-note">
          <div className="focus-note-label">Подсказка</div>
          <p>В журнале достаточно даты, номера заявки и услуги. Остальное не нужно для выгрузки.</p>
        </div>

        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => setIsImportOpen((current) => !current)}
        >
          {isImportOpen ? "Скрыть импорт" : "Массовый импорт"}
        </button>

        {isImportOpen && <JournalBulkImportForm initialWorkDate={draft.work_date} />}

        {error && <div className="form-error">{error}</div>}
        <div className="page-sub" style={{ marginTop: -2 }}>
          Черновик сохраняется автоматически
        </div>
        <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
          {isSubmitting ? "Сохранение..." : "+ Запись"}
        </button>
      </form>
    </CollapsiblePanel>
  );
}
