"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { JournalEntryModal } from "@/components/journal-entry-modal";

type Props = {
  entryId: string;
  ticketNumber: string | null;
  activityType: string;
  status: string;
  startedAt: string | null;
  endedAt: string | null;
  currentDescription: string | null;
  currentResolution: string | null;
  currentContact: string | null;
};

export function JournalEntryActions({
  entryId,
  ticketNumber,
  activityType,
  status,
  startedAt,
  endedAt,
  currentDescription,
  currentResolution,
  currentContact,
}: Props) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  async function onDelete() {
    if (!window.confirm("Удалить запись?")) return;
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

  return (
    <>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <button type="button" className="btn btn-sm" onClick={() => setIsModalOpen(true)} disabled={isLoading}>
          Подробно
        </button>
        <button type="button" className="btn btn-sm btn-danger" onClick={onDelete} disabled={isLoading}>
          Удалить
        </button>
        {error && <span className="form-error">{error}</span>}
      </div>

      {isModalOpen && (
        <JournalEntryModal
          entryId={entryId}
          ticketNumber={ticketNumber}
          activityType={activityType}
          status={status}
          startedAt={startedAt}
          endedAt={endedAt}
          description={currentDescription}
          resolution={currentResolution}
          contact={currentContact}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </>
  );
}
