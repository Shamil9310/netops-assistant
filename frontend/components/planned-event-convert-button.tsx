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
      const body = (await response.json()) as { detail?: string };
      if (!response.ok) {
        setError(body.detail ?? "Не удалось конвертировать");
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
      {error && <span className="form-error">{error}</span>}
    </div>
  );
}
