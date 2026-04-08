"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Props = {
  eventId: string;
};

export function PlannedEventConvertButton({ eventId }: Props) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onConvert() {
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await fetch(`/api/planned-events/${eventId}/convert`, {
        method: "POST",
      });
      const responsePayload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        setError(responsePayload.detail ?? "Не удалось конвертировать");
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
    if (!window.confirm("Удалить плановое событие?")) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await fetch(`/api/planned-events/${eventId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const responsePayload = (await response.json()) as { detail?: string };
        setError(responsePayload.detail ?? "Ошибка удаления");
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
      <button type="button" className="btn btn-sm btn-danger" onClick={onDelete} disabled={isSubmitting}>
        Удалить
      </button>
      {error && <span className="form-error">{error}</span>}
    </div>
  );
}
