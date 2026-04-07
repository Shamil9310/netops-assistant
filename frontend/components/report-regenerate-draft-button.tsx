"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Props = {
  reportId: string;
};

export function ReportRegenerateDraftButton({ reportId }: Props) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onRegenerate() {
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await fetch("/api/reports/regenerate-draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId }),
      });
      const body = (await response.json()) as { report_id?: string; detail?: string };
      if (!response.ok || !body.report_id) {
        setError(body.detail ?? "Не удалось создать новую draft-версию");
        return;
      }
      router.push(`/reports?report_id=${body.report_id}`);
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <button type="button" className="btn btn-sm" onClick={onRegenerate} disabled={isSubmitting}>
        {isSubmitting ? "Пересборка..." : "Пересобрать в draft"}
      </button>
      {error && <span className="form-error">{error}</span>}
    </div>
  );
}
