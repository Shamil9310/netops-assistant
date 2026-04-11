"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { extractErrorMessage } from "@/lib/api-error";

type Props = {
  entryId: string;
};

export function JournalEntryActions({
  entryId,
}: Props) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onDelete() {
    if (!window.confirm("Удалить запись?")) return;
    setError(null);
    setIsLoading(true);
    try {
      const response = await fetch(`/api/journal/entries/${entryId}`, { method: "DELETE" });
      if (!response.ok) {
        const responsePayload = (await response.json()) as unknown;
        setError(extractErrorMessage(responsePayload, "Ошибка удаления"));
        return;
      }
      window.location.reload();
    } catch {
      setError("Ошибка удаления");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
      <Link
        href={`/journal/entries/${entryId}`}
        className="btn btn-sm"
        target="_blank"
        rel="noreferrer"
      >
        Подробно
      </Link>
      <button type="button" className="btn btn-sm btn-danger" onClick={onDelete} disabled={isLoading}>
        Удалить
      </button>
      {error && <span className="form-error">{error}</span>}
    </div>
  );
}
