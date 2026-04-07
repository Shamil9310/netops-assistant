"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Props = {
  reportId: string;
};

export function ReportFinalizeButton({ reportId }: Props) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onFinalize() {
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await fetch("/api/reports/finalize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId }),
      });
      const body = (await response.json()) as { detail?: string };
      if (!response.ok) {
        setError(body.detail ?? "Не удалось зафиксировать отчёт");
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
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <button type="button" className="btn btn-sm" onClick={onFinalize} disabled={isSubmitting}>
        {isSubmitting ? "Фиксация..." : "Зафиксировать (final)"}
      </button>
      {error && <span className="form-error">{error}</span>}
    </div>
  );
}
