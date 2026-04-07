"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type Props = {
  entryId: string;
  currentTitle: string;
  currentDescription: string | null;
};

export function JournalEntryActions({ entryId, currentTitle, currentDescription }: Props) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onDelete() {
    setError(null);
    setIsLoading(true);
    try {
      const response = await fetch(`/api/journal/entries/${entryId}`, { method: "DELETE" });
      if (!response.ok) {
        const body = (await response.json()) as { detail?: string };
        setError(body.detail ?? "Ошибка удаления");
        return;
      }
      router.refresh();
    } catch {
      setError("Ошибка удаления");
    } finally {
      setIsLoading(false);
    }
  }

  async function onQuickEdit() {
    const nextTitle = window.prompt("Новый заголовок", currentTitle)?.trim();
    if (!nextTitle) {
      return;
    }
    const nextDescription = window.prompt("Новое описание", currentDescription ?? "") ?? "";

    setError(null);
    setIsLoading(true);
    try {
      const response = await fetch(`/api/journal/entries/${entryId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: nextTitle,
          description: nextDescription || null,
        }),
      });
      if (!response.ok) {
        const body = (await response.json()) as { detail?: string };
        setError(body.detail ?? "Ошибка обновления");
        return;
      }
      router.refresh();
    } catch {
      setError("Ошибка обновления");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
      <button type="button" className="btn btn-sm" onClick={onQuickEdit} disabled={isLoading}>
        Ред.
      </button>
      <button type="button" className="btn btn-sm btn-danger" onClick={onDelete} disabled={isLoading}>
        Удалить
      </button>
      {error && <span className="form-error">{error}</span>}
    </div>
  );
}
