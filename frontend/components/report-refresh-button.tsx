"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Props = {
  reportId: string;
};

export function ReportRefreshButton({ reportId }: Props) {
  const router = useRouter();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onRefresh() {
    setError(null);
    setIsRefreshing(true);
    try {
      const response = await fetch("/api/reports/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId }),
      });
      const responsePayload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        setError(responsePayload.detail ?? "Не удалось обновить отчёт");
        return;
      }
      router.refresh();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsRefreshing(false);
    }
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <button type="button" className="btn btn-sm" onClick={onRefresh} disabled={isRefreshing}>
        {isRefreshing ? "Обновление..." : "Обновить отчёт"}
      </button>
      {error && <span className="form-error">{error}</span>}
    </div>
  );
}
