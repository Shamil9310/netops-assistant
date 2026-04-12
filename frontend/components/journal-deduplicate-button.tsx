"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { extractErrorMessage } from "@/lib/api-error";

type Props = {
  duplicateCount: number;
  workDate: string;
};

type DeduplicationResponse = {
  work_date: string;
  removed: number;
  duplicate_ticket_numbers: string[];
};

export function JournalDeduplicateButton({ duplicateCount, workDate }: Props) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  async function onDeduplicate() {
    if (duplicateCount === 0) {
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`/api/journal/entries/deduplicate?work_date=${workDate}`, {
        method: "POST",
      });
      const responsePayload = (await response.json()) as DeduplicationResponse | unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось удалить дубли"));
        return;
      }

      const deduplicationResult = responsePayload as DeduplicationResponse;
      setSuccess(`Удалено дублей: ${deduplicationResult.removed}`);
      router.refresh();
    } catch {
      setError("Ошибка удаления дублей");
    } finally {
      setIsSubmitting(false);
    }
  }

  // Кнопка живёт рядом с фильтром даты, потому что действие относится
  // именно к текущему дню журнала, а не ко всему архиву пользователя.
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <button
        type="button"
        className="btn btn-sm"
        onClick={() => setIsConfirmOpen(true)}
        disabled={isSubmitting || duplicateCount === 0}
        title={
          duplicateCount === 0
            ? "За выбранную дату дубли по номеру заявки не найдены"
            : "Удалить повторные записи с одинаковым номером заявки"
        }
      >
        {isSubmitting ? "Удаление..." : `Удалить дубли (${duplicateCount})`}
      </button>
      {error && <span className="form-error">{error}</span>}
      {success && <span className="form-success">{success}</span>}
      <ConfirmDialog
        open={isConfirmOpen}
        title="Удалить дубли?"
        description="Будут удалены только повторные записи по номеру заявки за выбранную дату."
        confirmLabel="Удалить дубли"
        onCancel={() => setIsConfirmOpen(false)}
        onConfirm={async () => {
          setIsConfirmOpen(false);
          await onDeduplicate();
        }}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}
