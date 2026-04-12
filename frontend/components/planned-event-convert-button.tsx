"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { extractErrorMessage } from "@/lib/api-error";

type Props = {
  eventId: string;
};

export function PlannedEventConvertButton({ eventId }: Props) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  async function onConvert() {
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await fetch(`/api/planned-events/${eventId}/convert`, {
        method: "POST",
      });
      const responsePayload = (await response.json()) as unknown;
      if (!response.ok) {
        setError(extractErrorMessage(responsePayload, "Не удалось конвертировать"));
        return;
      }
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onDelete() {
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await fetch(`/api/planned-events/${eventId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const responsePayload = (await response.json()) as unknown;
        setError(extractErrorMessage(responsePayload, "Ошибка удаления"));
        return;
      }
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <button type="button" className="btn btn-sm" onClick={onConvert} disabled={isSubmitting}>
        В журнал
      </button>
      <button type="button" className="btn btn-sm btn-danger" onClick={() => setIsConfirmOpen(true)} disabled={isSubmitting}>
        Удалить
      </button>
      {error && <span className="form-error">{error}</span>}
      <ConfirmDialog
        open={isConfirmOpen}
        title="Удалить плановое событие?"
        description="Событие исчезнет из плана дня и восстановить его будет нельзя."
        confirmLabel="Удалить"
        onCancel={() => setIsConfirmOpen(false)}
        onConfirm={async () => {
          setIsConfirmOpen(false);
          await onDelete();
        }}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}
